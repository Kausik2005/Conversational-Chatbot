import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import datetime
import time

from langchain_ollama import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_core.messages import HumanMessage, AIMessage

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title='Conversational QA ChatBot',
                   page_icon=':brain:',
                   layout='centered',
                   initial_sidebar_state='auto')

#load_dotenv()

Chat_History_DIR = "chat_histories"
Vector_Store_DIR = "vector_stores"
Scraped_Content_Dir = "scraped_content"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


for dir_path in [Chat_History_DIR, Vector_Store_DIR, Scraped_Content_Dir]:

    if not os.path.exists(dir_path):
        
        os.makedirs(dir_path)

llm = ChatOllama(model="llama3:8b")

def save_chat_history(messages, chat_id):

    file_path = os.path.join(Chat_History_DIR, f"{chat_id}.json")
    
    with open(file_path,"w", encoding = 'utf-8') as f:
        history_data = [{"type":msg.type, "content":msg.content} for msg in messages]
        json.dump(history_data, f, indent =4)


def load_chat_history(chat_id):

    file_path = os.path.join(Chat_History_DIR, f"{chat_id}.json")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding = "utf-8") as f:
            history_data = json.load(f)
            messages = []
            for item in history_data:
                if item["type"] == "human":
                    messages.append(HumanMessage(content=item["content"]))
                elif item["type"] == "ai":
                    messages.append(AIMessage(content=item["content"]))
            return messages
        
    return[]


def get_sorted_chat_ids():

    files = os.listdir(Chat_History_DIR)
    chat_ids = [f.split('.json')[0] for f in files if f.endswith('.json')]
    chat_ids.sort(
        key = lambda x: os.path.getmtime(os.path.join(Chat_History_DIR, f"{x}.json")),
        reverse = True
    )

    return chat_ids


def load_selected_chat(chat_id):

    vector_store_path = os.path.join(Vector_Store_DIR, chat_id)

    if os.path.exists(vector_store_path):
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
        st.session_state.chain = build_rag_chain(vector_store.as_retriever())

        st.session_state.current_chat_id = chat_id
        st.session_state.messages = load_chat_history(chat_id)
        st.success("Conversation context restored! For better results process the document again.")
    
    else:
        start_new_chat()
        st.error("Could not find the context for this chat. Starting a new chat.")
        time.sleep(3)


def start_new_chat():

    st.session_state.current_chat_id = None
    st.session_state.messages = []
    st.session_state.chain = None


def get_summary_as_id(question, answer , llm):
    
    summary_system_prompt = """You are an expert sumarizer.
    Your task is to create a concise, 3 to 5 word filename based on the user's question and the ai's answer.
    Use underscores instead of spaces. Do not use any special characters other than underscores.
    Be concise and accurate.
    Try to use simple english if possible
    
    EXAMPLE:
    - Question: "How do I use pandas in Python?"
    - Answer: "You import it and use DataFrames."
    - CORRECT FILENAME: "Pandas_DataFrame_Usage"
    """
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", summary_system_prompt),
        ("human", "Question: \"{question}\"\nAnswer: \"{answer}\"")
    ])

    summary_chain = summary_prompt | llm
    summary = summary_chain.invoke({"question": question, "answer": answer}).content

    sanitized_summary = "".join(c for c in summary if c.isalnum() or c == "_")

    timestamp = datetime.datetime.now().strftime("%d%m%Y%H%M%S")

    if not sanitized_summary:
        sanitized_summary = "Chat_Summary"

    return f"{sanitized_summary}_{timestamp}"


# --- SESSION STATE INITIALIZATION ---
if "chain" not in st.session_state:
    st.session_state.chain = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


# --- PROMPT TEMPLATES ---
# 1. Prompt for question reformulation based on history
context_q_system_prompt = """Given a chat history and the latest user question
which might reference context in the chat history, formulate a standalone question
which can be understood without the chat history. Do NOT answer the question,
just reformulate it if needed and otherwise return it as is."""

context_q_prompt = ChatPromptTemplate.from_messages([
    ("system", context_q_system_prompt),
    MessagesPlaceholder("chathistory"),
    ("human", "{input}")
])


# 2. Prompt for answering the question based on retrieved context
qa_system_prompt = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Context: {context}"""


qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("chathistory"),
    ("human", "{input}")
])


# --- HELPER FUNCTIONS ---
def get_documents_from_files(uploaded_files):

    """Loads documents from a list of uploaded files (PDF, DOCX)."""
    all_docs = []
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            temp_file.write(file.getvalue())
            temp_file_path = temp_file.name
        
        try:
            if file.type == "application/pdf":
                loader = PyMuPDFLoader(temp_file_path)
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                loader = Docx2txtLoader(temp_file_path)
            else:
                st.warning(f"Unsupported file type: {file.name}", icon="⚠️")
                continue
            all_docs.extend(loader.load())
        finally:
            os.remove(temp_file_path)

    return all_docs


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain.schema import Document


def fetch_html(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    return resp.text


def clean_text(soup):

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def scrape_page(url):

    try:
        html = fetch_html(url)

    except Exception as e:
        print(f"Failed to fetch {url}: {e}")

        return {"url": url, "text": "", "links": []}

    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup)

    links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
    links = [l for l in links if l.startswith("http")]

    return {"url": url, "text": text, "links": links}


def scrape_with_links(start_url):

    visited = set()
    docs = []
    domain = urlparse(start_url).netloc

    # scrape main page
    main = scrape_page(start_url)
    if main["text"]:
        docs.append(Document(page_content=main["text"], metadata={"source": main["url"]}))
    visited.add(start_url)

    # scrape linked pages (same domain only)
    for link in main["links"]:
        if link not in visited and urlparse(link).netloc == domain:
            page = scrape_page(link)
            if page["text"]:
                docs.append(Document(page_content=page["text"], metadata={"source": page["url"]}))
            visited.add(link)

    st.info(f"Retrieved {len(docs)} pages from {domain}")

    if docs:
        save_dir = "scrapped_content"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        file_path = os.path.join(save_dir, f"{domain}.json")

        docs_as_dict_list = [
            {"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(docs_as_dict_list, f, indent = 4)
        
        st.success(f"Scraped content saved to {file_path}")

    return docs


def build_rag_chain(retriever):

    history_aware_retriever = create_history_aware_retriever(llm, retriever, context_q_prompt)
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)

    return create_retrieval_chain(history_aware_retriever, qa_chain)


def process_documents_and_create_chain(docs):

    """Splits documents, creates a vector store, and builds the conversational RAG chain."""
    if not docs:
        st.warning("No processable documents found.", icon="⚠️")

        return

    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"temp_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    vector_store_path = os.path.join(Vector_Store_DIR, st.session_state.current_chat_id)

    # Create vector store
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    split_documents = text_splitter.split_documents(docs)
    vector_store = FAISS.from_documents(split_documents, embeddings)
    
    vector_store.save_local(vector_store_path)
    #history_aware_retriever = create_history_aware_retriever(llm, retriever, context_q_prompt)
    #qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    #st.session_state.chain = create_retrieval_chain(history_aware_retriever, qa_chain)
    st.session_state.chain = build_rag_chain(vector_store.as_retriever())
    st.success("Documents processed and ready for questions!")


def clear_chat_history():

    st.session_state.messages = []
    st.session_state.chain = None

    
# --- SIDEBAR ---
with st.sidebar:

    st.title("Data Source")
    source_choice = st.radio("Choose your data source:", ("Upload a Document", "Fetch from URL"))
    
    if source_choice == "Upload a Document":

        uploaded_files = st.file_uploader("Upload your documents", accept_multiple_files=True, type=['pdf', 'docx'])

        if st.button("Process Documents", use_container_width=True):

            with st.spinner("Processing..."):

                if uploaded_files:

                    docs = get_documents_from_files(uploaded_files)
                    process_documents_and_create_chain(docs)

                else:

                    st.warning("Please upload at least one document.", icon="⚠️")

    elif source_choice == "Fetch from URL":

        url = st.text_input("Enter the URL", placeholder="https://example.com")

        if st.button("Process URL", use_container_width=True):

            with st.spinner("Fetching and processing..."):

                if url:

                    docs = scrape_with_links(url)
                    process_documents_and_create_chain(docs)

                else:

                    st.warning("Please enter a valid URL.", icon="⚠️")

    st.markdown("---")
    st.button('➕ New Chat', on_click=start_new_chat, use_container_width=True)
    st.markdown('## Recent Chats')

    sorted_chat_ids = get_sorted_chat_ids()

    for chat_id in sorted_chat_ids:

        parts = chat_id.split('_')

        summary_part = " ".join(parts[:-1])
        display_name = summary_part.strip()

        if st.button(display_name, key = chat_id, use_container_width=True):

            load_selected_chat(chat_id)
            st.rerun()


# --- MAIN CHAT INTERFACE ---
st.title("Conversational ChatBot 🧠")
st.markdown("Provide your documents or a URL, then ask any questions!")


# Display chat messages
for message in st.session_state.messages:

    with st.chat_message(message.type):

        st.write(message.content)


# Handles user input
if user_prompt := st.chat_input("Ask a question about your documents:"):

    if st.session_state.chain is None:

        st.warning("Please process a document or URL first.", icon="⚠️")

    else:

        st.session_state.messages.append(HumanMessage(content=user_prompt))

        with st.chat_message("human"):

            st.write(user_prompt)

        is_new_chat = "temp_" in st.session_state.current_chat_id

        with st.spinner("Thinking..."):

            try:

                response = st.session_state.chain.invoke({
                    "chathistory": st.session_state.messages.copy(),
                    "input": user_prompt
                })

                answer = response.get("answer", "Could not generate an answer.")

                if is_new_chat:

                    with st.spinner("Generating chat title..."):

                        new_chat_id = get_summary_as_id(user_prompt, answer, llm)

                        temp_path = os.path.join(Vector_Store_DIR, st.session_state.current_chat_id)
                        new_path = os.path.join(Vector_Store_DIR, new_chat_id)
                        os.rename(temp_path, new_path)

                        st.session_state.current_chat_id = new_chat_id

                st.session_state.messages.append(AIMessage(content=answer))

                with st.chat_message("ai"):

                    st.write(answer)

                save_chat_history(st.session_state.messages, st.session_state.current_chat_id)
                
                st.rerun()

            except Exception as e:

                error_message = f"An error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append(AIMessage(content=error_message))

                with st.chat_message("ai"):

                    st.write(error_message)
