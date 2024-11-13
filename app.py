# app.py
import streamlit as st
from googleapiclient.discovery import build
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Replace with your actual API Key
API_KEY = 'AIzaSyDtHJl7ndki0dd1b9JPyN57tRg2YALo5ls'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def extract_channel_id(channel_url):
    if 'channel/' in channel_url:
        return channel_url.split('channel/')[1].split('/')[0]
    elif '@' in channel_url:
        username = channel_url.split('@')[1].split('/')[0]
        return get_channel_id_from_username(username)
    return None

def get_channel_id_from_username(username):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    search_response = youtube.search().list(
        part='snippet',
        q=username,
        type='channel',
        maxResults=1
    ).execute()
    if 'items' in search_response and len(search_response['items']) > 0:
        return search_response['items'][0]['snippet']['channelId']
    return None

def is_short_video(duration):
    match = re.match(r"PT(\d+)S", duration)
    if match:
        seconds = int(match.group(1))
        return seconds < 60
    return False

def get_channel_info(channel_url):
    channel_id = extract_channel_id(channel_url)
    if not channel_id:
        st.error("Invalid channel URL.")
        return

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    
    channel_response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    ).execute()

    if 'items' not in channel_response or len(channel_response['items']) == 0:
        st.error("Channel not found.")
        return

    channel_info = channel_response['items'][0]['snippet']
    channel_stats = channel_response['items'][0]['statistics']

    st.write("## Channel Information")
    st.write(f"**Channel Title**: {channel_info['title']}")
    st.write(f"**Description**: {channel_info['description']}")
    st.write(f"**Subscribers**: {channel_stats.get('subscriberCount', 'Hidden')}")
    st.write(f"**Total Views**: {channel_stats['viewCount']}")

    video_response = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=5,
        order='date'
    ).execute()

    latest_full_length_video = None
    for video in video_response['items']:
        video_id = video['id'].get('videoId', None)
        if video_id:
            video_details = youtube.videos().list(
                part='contentDetails',
                id=video_id
            ).execute()

            duration = video_details['items'][0]['contentDetails']['duration']
            if not is_short_video(duration):
                latest_full_length_video = video
                break

    if latest_full_length_video:
        video_snippet = latest_full_length_video['snippet']
        video_id = latest_full_length_video['id']['videoId']

        st.write("\n## Latest Full-Length Video")
        st.write(f"**Title**: {video_snippet['title']}")
        st.write(f"**Published At**: {video_snippet['publishedAt']}")
        st.write(f"**Video URL**: [Watch here](https://www.youtube.com/watch?v={video_id})")

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            paragraph_text = ' '.join([entry['text'] for entry in transcript])
            st.write("## Transcript")
            st.text(paragraph_text)
        except Exception as e:
            st.error(f"Error fetching transcript: {e}")
    else:
        st.warning("No full-length videos found.")

# Streamlit UI
st.title("YouTube Channel Info App")
channel_url = st.text_input("Enter the YouTube channel URL:")

if st.button("Fetch Channel Info"):
    if channel_url:
        get_channel_info(channel_url)
    else:
        st.warning("Please enter a valid channel URL.")
