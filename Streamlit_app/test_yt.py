# File: test_yt.py

from youtube_transcript_api import YouTubeTranscriptApi
import sys

print("--- Checking Python Environment ---")
print(f"Python Executable: {sys.executable}")
print("-" * 30)

try:
    # Using a different, highly available video ID for testing
    video_id = "dQw4w9WgXcQ" 

    print(f"Attempting to fetch transcript for video ID: {video_id}")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    print("\n✅ SUCCESS: Transcript fetched successfully!")
    print("The library is installed correctly for this Python environment.")

except Exception as e:
    print(f"\n❌ FAILED: An error occurred.")
    print(f"Error details: {e}")