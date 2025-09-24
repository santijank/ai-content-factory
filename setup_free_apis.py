#!/usr/bin/env python3
"""
Setup Guide for Free Tier APIs
แนะนำการติดตั้ง APIs ฟรีสำหรับ AI Content Factory
"""

def setup_google_trends():
    """ติดตั้ง Google Trends (ฟรี)"""
    print("1. Google Trends (ฟรี - ไม่ต้อง API key)")
    print("=" * 50)
    print("pip install pytrends")
    print()
    
    sample_code = '''
# ตัวอย่างการใช้งาน Google Trends
from pytrends.request import TrendReq
import pandas as pd

def get_trending_topics():
    pytrends = TrendReq(hl='en-US', tz=360)
    
    # ดู trending searches
    trending_searches = pytrends.trending_searches(pn='thailand')
    print("Trending in Thailand:", trending_searches.head(10))
    
    # ดูข้อมูล keyword specific
    pytrends.build_payload(['AI', 'ChatGPT', 'Technology'], 
                          cat=0, timeframe='today 3-m', geo='TH', gprop='')
    interest_over_time = pytrends.interest_over_time()
    return interest_over_time

# ใช้งาน
trends = get_trending_topics()
'''
    
    with open('google_trends_example.py', 'w', encoding='utf-8') as f:
        f.write(sample_code)
    
    print("✅ สร้างไฟล์ google_trends_example.py")
    print("⚠️ ข้อจำกัด: Rate limiting, ต้องระวัง IP blocking")

def setup_youtube_api():
    """ติดตั้ง YouTube Data API (ฟรี 10,000 requests/วัน)"""
    print("\n2. YouTube Data API v3 (ฟรี 10,000 requests/วัน)")
    print("=" * 50)
    print("Steps:")
    print("1. ไปที่ https://console.cloud.google.com/")
    print("2. สร้าง Project ใหม่")
    print("3. เปิด YouTube Data API v3")
    print("4. สร้าง API Key")
    print("5. pip install google-api-python-client")
    print()
    
    sample_code = '''
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
'''
    
    with open('youtube_api_example.py', 'w', encoding='utf-8') as f:
        f.write(sample_code)
    
    print("✅ สร้างไฟล์ youtube_api_example.py")

def setup_groq_api():
    """ติดตั้ง Groq API (ฟรี tier)"""
    print("\n3. Groq API (ฟรี tier)")
    print("=" * 50)
    print("Steps:")
    print("1. ไปที่ https://console.groq.com/")
    print("2. สร้างบัญชี")
    print("3. สร้าง API Key")
    print("4. pip install groq")
    print()
    
    sample_code = '''
# ตัวอย่างการใช้งาน Groq API
from groq import Groq
import os

def analyze_trend_with_groq(trend_data):
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    prompt = f"""
    วิเคราะห์ trend นี้และให้คำแนะนำการสร้างเนื้อหา:
    
    Topic: {trend_data['topic']}
    Views: {trend_data.get('views', 'N/A')}
    
    ให้ผลลัพธ์ในรูปแบบ JSON:
    {{
        "content_angles": ["มุมมอง 1", "มุมมอง 2", "มุมมอง 3"],
        "target_audience": "กลุ่มเป้าหมาย",
        "estimated_engagement": "สูง/กลาง/ต่ำ",
        "suggested_format": "วิดีโอ/บทความ/โพสต์",
        "hashtags": ["#tag1", "#tag2", "#tag3"]
    }}
    """
    
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    return completion.choices[0].message.content

# ใช้งาน
trend = {"topic": "AI Tools 2024", "views": 150000}
analysis = analyze_trend_with_groq(trend)
'''
    
    with open('groq_api_example.py', 'w', encoding='utf-8') as f:
        f.write(sample_code)
    
    print("✅ สร้างไฟล์ groq_api_example.py")

def setup_openai_api():
    """ติดตั้ง OpenAI API (pay-per-use, เริ่มต้นราคาถูก)"""
    print("\n4. OpenAI API (pay-per-use, เริ่มต้น $5)")
    print("=" * 50)
    print("Steps:")
    print("1. ไปที่ https://platform.openai.com/")
    print("2. สร้างบัญชี")
    print("3. เติมเงิน $5 (น้อยสุด)")
    print("4. สร้าง API Key")
    print("5. pip install openai")
    print()
    
    sample_code = '''
# ตัวอย่างการใช้งาน OpenAI API
from openai import OpenAI
import os

def generate_content_script(topic, angle):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""
    สร้าง script สำหรับวิดีโอ YouTube ความยาว 3-5 นาที:
    
    หัวข้อ: {topic}
    มุมมอง: {angle}
    
    รูปแบบ script:
    1. Hook (15 วินาทีแรก)
    2. เนื้อหาหลัก (3-4 นาที)
    3. Call to Action (30 วินาทีสุดท้าย)
    
    เขียนให้น่าสนใจและเหมาะกับ YouTube algorithm
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

# ใช้งาน
script = generate_content_script("AI Tools 2024", "เครื่องมือ AI ที่ช่วยงานได้จริง")
'''
    
    with open('openai_api_example.py', 'w', encoding='utf-8') as f:
        f.write(sample_code)
    
    print("✅ สร้างไฟล์ openai_api_example.py")

def update_env_file():
    """อัปเดตไฟล์ .env"""
    print("\n5. อัปเดตไฟล์ .env")
    print("=" * 50)
    
    env_content = '''# AI Content Factory Environment Variables
DATABASE_URL=sqlite:///content_factory.db

# Free Tier API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Pay-per-use APIs (เริ่มต้นด้วยเงินน้อย)
OPENAI_API_KEY=your_openai_api_key_here

# Google Trends (ไม่ต้อง API key)
# ใช้ pytrends library โดยตรง

# Flask Settings
FLASK_ENV=development
FLASK_PORT=5000
'''
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ อัปเดตไฟล์ .env.example แล้ว")
    print("📝 คัดลอกเป็น .env และใส่ API keys จริง")

def create_requirements():
    """สร้าง requirements.txt สำหรับ APIs"""
    requirements = '''# AI Content Factory - API Dependencies
flask==3.1.2
requests==2.31.0
python-dotenv==1.0.0
sqlite3

# Data Sources (ฟรี)
pytrends==4.9.2
google-api-python-client==2.108.0

# AI Services
groq==0.4.1
openai==1.3.7

# Optional (สำหรับ advanced features)
beautifulsoup4==4.12.2
pandas==2.1.4
matplotlib==3.8.2
'''
    
    with open('requirements_with_apis.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("\n✅ สร้างไฟล์ requirements_with_apis.txt")
    print("📦 ติดตั้งด้วย: pip install -r requirements_with_apis.txt")

def main():
    """รันการ setup ทั้งหมด"""
    print("🆓 Free Tier APIs Setup Guide")
    print("=" * 60)
    print("การเริ่มต้นด้วย APIs ฟรีและราคาถูก")
    print()
    
    setup_google_trends()
    setup_youtube_api()
    setup_groq_api()
    setup_openai_api()
    update_env_file()
    create_requirements()
    
    print("\n📋 สรุปค่าใช้จ่าย:")
    print("💰 Google Trends: ฟรี")
    print("💰 YouTube API: ฟรี (10,000 requests/วัน)")
    print("💰 Groq API: ฟรี tier")
    print("💰 OpenAI API: ~200-500 บาท/เดือน (ใช้น้อย)")
    print("💰 รวม: 200-500 บาท/เดือน")
    
    print("\n🎯 ขั้นตอนถัดไป:")
    print("1. สมัครและเอา API keys มาใส่ใน .env")
    print("2. ติดตั้ง dependencies: pip install -r requirements_with_apis.txt")
    print("3. ทดสอบ APIs ด้วยไฟล์ example")
    print("4. อัปเดตระบบให้ใช้ real data")

if __name__ == "__main__":
    main()