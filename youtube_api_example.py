
# ตัวอย่างการใช้งาน YouTube API
from googleapiclient.discovery import build
import os

def get_youtube_trending():
    api_key = os.getenv('YOUTUBE_API_KEY')
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # ดู trending videos
    request = youtube.videos().list(
        part='snippet,statistics',
        chart='mostPopular',
        regionCode='TH',
        maxResults=50
    )
    
    response = request.execute()
    
    trending_videos = []
    for item in response['items']:
        video_data = {
            'title': item['snippet']['title'],
            'views': int(item['statistics']['viewCount']),
            'likes': int(item['statistics'].get('likeCount', 0)),
            'category': item['snippet']['categoryId']
        }
        trending_videos.append(video_data)
    
    return trending_videos

# ใช้งาน
videos = get_youtube_trending()
