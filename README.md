# Conversational RAG Chatbot

A conversational AI chatbot built using **Streamlit**, **LangChain**, **Ollama**, and **FAISS** that allows users to chat with uploaded documents or website content using Retrieval-Augmented Generation (RAG).

---

# Features

* Upload and chat with:

  * PDF documents
  * DOCX files
* Fetch and process website content from URLs
* Conversational memory with chat history
* Retrieval-Augmented Generation (RAG)
* Vector embeddings using HuggingFace
* Local LLM support using Ollama
* Persistent FAISS vector storage
* Automatic chat title generation
* Multi-session chat management

---

# Tech Stack

## Frontend

* Streamlit

## Backend / AI

* LangChain
* Ollama
* HuggingFace Embeddings
* FAISS Vector Database

## Document Processing

* PyMuPDF
* Docx2txt
* BeautifulSoup4

---

# Project Architecture

```text
User Uploads Document / URL
            │
            ▼
Document Loader / Web Scraper
            │
            ▼
Text Chunking
            │
            ▼
HuggingFace Embeddings
            │
            ▼
FAISS Vector Store
            │
            ▼
LangChain Retrieval Chain
            │
            ▼
Ollama LLM Response
            │
            ▼
Streamlit Chat Interface
```

---

# Supported Inputs

## Document Upload

* PDF
* DOCX

## URL Processing

* Scrapes webpage content
* Extracts internal links
* Processes linked pages from same domain

---

# Installation

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd conversational-rag-chatbot
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Ollama

Download and install Ollama:

https://ollama.com

---

## 5. Pull the LLM Model

```bash
ollama pull llama3:8b
```

---

# Run the Application

```bash
streamlit run app.py
```

---

# How It Works

## Step 1: Upload Documents or Provide URL

Users can:

* Upload PDFs/DOCX files
* Enter a website URL

---

## Step 2: Document Processing

The application:

* Extracts text
* Splits into chunks
* Generates embeddings
* Stores vectors in FAISS

---

## Step 3: Conversational Retrieval

LangChain:

* Retrieves relevant chunks
* Uses chat history for contextual understanding
* Sends context to Ollama LLM

---

## Step 4: AI Response Generation

The chatbot generates concise answers based on:

* Uploaded content
* Previous conversation history

---

# Folder Structure

```text
project/
│
├── app.py
├── chat_histories/
├── vector_stores/
├── scraped_content/
├── requirements.txt
└── README.md
```

---

# Key Components

## 1. Conversational Memory

* Stores chat history locally
* Reloads previous conversations

## 2. Vector Database

* FAISS used for semantic retrieval
* Persistent storage for faster reloads

## 3. History-Aware Retrieval

* Reformulates user queries using previous chat history

## 4. Website Scraping

* Scrapes webpage text
* Follows internal links from same domain

---

# Libraries Used

| Library                | Purpose             |
| ---------------------- | ------------------- |
| Streamlit              | Web Interface       |
| LangChain              | RAG Pipeline        |
| Ollama                 | Local LLM Inference |
| FAISS                  | Vector Database     |
| HuggingFace Embeddings | Text Embeddings     |
| BeautifulSoup4         | Web Scraping        |
| PyMuPDF                | PDF Processing      |
| Docx2txt               | DOCX Parsing        |

---

# Future Improvements

* Multi-user authentication
* Cloud deployment
* Streaming responses
* Support for more file formats
* Advanced metadata filtering
* Hybrid search retrieval
* GPU acceleration
* Citation-based responses

---

# Example Use Cases

* Research assistant
* Company knowledge base
* PDF question answering
* Website chatbot
* Personal AI assistant
* Educational tutor

---

# Author

Kausik Varma

---

# License

This project is for educational and personal learning purposes.
