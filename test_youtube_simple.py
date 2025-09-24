# test_youtube_simple.py - ทดสอบ YouTube API แบบง่ายๆ

import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# โหลด environment variables
load_dotenv()

def test_youtube_api():
    """ทดสอบ YouTube API แบบง่ายๆ"""
    
    # ดึง API key จาก environment
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ ไม่พบ YOUTUBE_API_KEY ในไฟล์ .env")
        return False
    
    try:
        print("🔑 API Key found:", api_key[:10] + "..." if len(api_key) > 10 else api_key)
        
        # สร้าง YouTube service
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("✅ YouTube service created successfully!")
        
        # ทดสอบ API call - ดึงวิดีโอยอดนิยมในไทย
        print("📺 Testing API call - Getting trending videos in Thailand...")
        
        request = youtube.videos().list(
            part='snippet,statistics',
            chart='mostPopular',
            regionCode='TH',
            maxResults=5
        )
        response = request.execute()
        
        print(f"✅ API call successful! Found {len(response['items'])} trending videos:")
        print()
        
        # แสดงผลวิดีโอที่ได้
        for i, video in enumerate(response['items'], 1):
            title = video['snippet']['title']
            channel = video['snippet']['channelTitle']
            views = int(video['statistics'].get('viewCount', 0))
            
            print(f"{i}. {title}")
            print(f"   📺 Channel: {channel}")
            print(f"   👀 Views: {views:,}")
            print()
        
        print("🎉 YouTube API integration working perfectly!")
        return True
        
    except HttpError as e:
        print(f"❌ YouTube API Error: {e}")
        if "API key" in str(e):
            print("💡 Tip: ตรวจสอบว่า API key ถูกต้องและเปิดใช้งาน YouTube Data API v3 แล้ว")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 YouTube API Quick Test")
    print("=" * 40)
    
    success = test_youtube_api()
    
    if success:
        print("\n🚀 Ready to proceed to next steps!")
        print("✅ YouTube API is working")
        print("✅ Can collect trending videos")
        print("✅ Ready for integration with main system")
    else:
        print("\n⚠️  Please fix the issues above before proceeding")