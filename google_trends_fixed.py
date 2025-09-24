#!/usr/bin/env python3
"""
Google Trends - Fixed Version
แก้ไขปัญหา rate limiting และ 404 errors
"""

from pytrends.request import TrendReq
import pandas as pd
import time
import random

def get_trending_topics_safe():
    """ดึงข้อมูล Google Trends แบบปลอดภัย"""
    try:
        # สร้าง TrendReq object ด้วย settings ที่ปลอดภัย
        pytrends = TrendReq(
            hl='en-US', 
            tz=360,
            timeout=(10, 25),
            retries=2,
            backoff_factor=0.1
        )
        
        print("🔍 กำลังดึงข้อมูล Google Trends...")
        
        # วิธีที่ 1: ใช้ interest_over_time แทน trending_searches
        keywords = ['AI', 'ChatGPT', 'Technology', 'YouTube', 'Content Creation']
        
        print(f"📊 วิเคราะห์ keywords: {keywords}")
        
        # Build payload
        pytrends.build_payload(
            keywords, 
            cat=0, 
            timeframe='today 3-m',  # 3 เดือนที่ผ่านมา
            geo='',  # ทั่วโลก แทน 'TH' เพื่อหลีกเลี่ยง geo restrictions
            gprop=''
        )
        
        # ดึงข้อมูล interest over time
        interest_over_time = pytrends.interest_over_time()
        
        if not interest_over_time.empty:
            print("✅ ดึงข้อมูล Interest Over Time สำเร็จ:")
            
            # คำนวณค่าเฉลี่ยของแต่ละ keyword
            avg_interest = interest_over_time.drop('isPartial', axis=1).mean().sort_values(ascending=False)
            
            for keyword, score in avg_interest.items():
                print(f"   {keyword}: {score:.1f}")
            
            return interest_over_time
        
        # หน่วงเวลาเพื่อหลีกเลี่ยง rate limiting
        time.sleep(random.uniform(1, 3))
        
        # วิธีที่ 2: ลอง related topics
        print("\n🔎 ค้นหา Related Topics...")
        related_topics = pytrends.related_topics()
        
        if related_topics:
            print("✅ พบ Related Topics:")
            for keyword, topics in related_topics.items():
                if topics['top'] is not None and not topics['top'].empty:
                    print(f"\n📈 {keyword} - Top Related:")
                    print(topics['top']['topic_title'].head(3).to_list())
        
        return interest_over_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 คำแนะนำ:")
        print("   - Google อาจบล็อก IP ชั่วคราว")
        print("   - ลองอีกครั้งในภายหลัง")
        print("   - ใช้ VPN หรือเปลี่ยน network")
        return None

def get_related_queries_safe(keyword="AI"):
    """ดึง related queries แบบปลอดภัย"""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        print(f"\n🔍 ค้นหา related queries สำหรับ: {keyword}")
        
        # Build payload สำหรับ keyword เดียว
        pytrends.build_payload([keyword], timeframe='today 1-m')
        
        # ดึง related queries
        related_queries = pytrends.related_queries()
        
        if related_queries and keyword in related_queries:
            queries = related_queries[keyword]
            
            if queries['top'] is not None:
                print("✅ Top Related Queries:")
                top_queries = queries['top']['query'].head(5).to_list()
                for i, query in enumerate(top_queries, 1):
                    print(f"   {i}. {query}")
                return top_queries
            
            if queries['rising'] is not None:
                print("📈 Rising Related Queries:")
                rising_queries = queries['rising']['query'].head(5).to_list()
                for i, query in enumerate(rising_queries, 1):
                    print(f"   {i}. {query}")
                return rising_queries
        
        return []
        
    except Exception as e:
        print(f"❌ Related queries error: {e}")
        return []

def get_sample_trends():
    """สร้างข้อมูล trends ตัวอย่างหาก Google Trends ไม่ทำงาน"""
    print("\n📋 ใช้ข้อมูลตัวอย่าง (Google Trends ไม่พร้อมใช้งาน)")
    
    sample_trends = {
        'AI Tools 2024': {'interest': 85, 'growth': '+15%', 'category': 'Technology'},
        'Content Creation': {'interest': 78, 'growth': '+12%', 'category': 'Media'},
        'YouTube Shorts': {'interest': 92, 'growth': '+25%', 'category': 'Entertainment'},
        'Digital Marketing': {'interest': 71, 'growth': '+8%', 'category': 'Business'},
        'ChatGPT': {'interest': 89, 'growth': '+18%', 'category': 'Technology'}
    }
    
    for topic, data in sample_trends.items():
        print(f"📊 {topic}: Interest {data['interest']}, Growth {data['growth']}")
    
    return sample_trends

def main():
    """รันการทดสอบ Google Trends"""
    print("🌐 Google Trends API Test (Fixed Version)")
    print("=" * 50)
    
    # ทดสอบ interest over time
    trends_data = get_trending_topics_safe()
    
    if trends_data is not None and not trends_data.empty:
        print("\n✅ Google Trends ทำงานปกติ")
        
        # ทดสอบ related queries
        time.sleep(2)  # หน่วงเวลาระหว่าง requests
        related = get_related_queries_safe("Technology")
        
    else:
        print("\n⚠️ Google Trends ไม่พร้อมใช้งาน")
        sample_data = get_sample_trends()
    
    print("\n💡 Tips สำหรับการใช้ Google Trends:")
    print("1. อย่าส่ง requests บ่อยเกินไป")
    print("2. ใช้ timeframe ที่เหมาะสม")
    print("3. หลีกเลี่ยงการใช้ geo specific หากมีปัญหา")
    print("4. มี backup plan ด้วย sample data")

if __name__ == "__main__":
    main()