import requests

# Test 1: A simple, reliable website
try:
    print("--- Testing connection to Google ---")
    response_google = requests.get("https://www.google.com", timeout=10)
    print(f"Google Status Code: {response_google.status_code}")
    if response_google.status_code == 200:
        print("✅ Connection to Google seems OK.")
    else:
        print("❌ Failed to connect to Google properly.")
except Exception as e:
    print(f"❌ An error occurred connecting to Google: {e}")

print("\n" + "-"*30 + "\n")

# Test 2: The YouTube watch page
try:
    print("--- Testing connection to YouTube ---")
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # Using a standard browser header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response_yt = requests.get(video_url, headers=headers, timeout=15)
    print(f"YouTube Status Code: {response_yt.status_code}")
    if response_yt.status_code == 200 and "html" in response_yt.headers.get('Content-Type', ''):
        print("✅ Connection to YouTube seems OK.")
    else:
        print("❌ Failed to connect to YouTube properly or received non-HTML content.")
except Exception as e:
    print(f"❌ An error occurred connecting to YouTube: {e}")