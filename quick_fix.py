# quick_fix.py - แก้ไขปัญหา Gemini Model และ Database

import sqlite3
import asyncio
import aiohttp
import json
import re

def fix_database():
    """แก้ไข database schema"""
    try:
        conn = sqlite3.connect('content_factory.db')
        cursor = conn.cursor()
        
        # เพิ่มคอลัมน์ที่ขาดหายไป
        try:
            cursor.execute('ALTER TABLE content_opportunities ADD COLUMN trend_topic TEXT')
            print("✅ Added trend_topic column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✅ trend_topic column already exists")
            else:
                print(f"❌ Error adding column: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Database fixed successfully")
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")

async def test_gemini_api():
    """ทดสอบ Gemini API ด้วย model ใหม่"""
    api_key = "AIzaSyDJakgTDs_YqhkGS1L7A6CimJl0MdaMI5U"
    
    # Models ใหม่ที่ใช้ได้
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-pro",
        "gemini-1.0-pro"
    ]
    
    for model in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": "Test message. Respond with just 'OK'"}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 100
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'candidates' in data:
                            content = data['candidates'][0]['content']['parts'][0]['text']
                            print(f"✅ {model}: Working - Response: {content.strip()}")
                            return model  # Return working model
                    else:
                        error_text = await response.text()
                        print(f"❌ {model}: Error {response.status}")
                        
        except Exception as e:
            print(f"❌ {model}: Exception - {e}")
    
    return None

async def test_trend_analysis():
    """ทดสอบการวิเคราะห์ trend ด้วย Gemini"""
    working_model = await test_gemini_api()
    
    if not working_model:
        print("❌ No working Gemini model found")
        return
    
    api_key = "AIzaSyDJakgTDs_YqhkGS1L7A6CimJl0MdaMI5U"
    
    prompt = """Analyze this trending topic:

Topic: AI Video Creation
Popularity: 85/100

Rate 1-10:
- viral_potential
- content_saturation  
- audience_interest
- monetization_opportunity

JSON only:
{"viral_potential": 8, "content_saturation": 6, "audience_interest": 9, "monetization_opportunity": 7, "content_angles": ["tutorial", "review", "tips"], "reasoning": "AI content is trending"}"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{working_model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 500
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ Gemini Analysis Response:")
                    print(content)
                    
                    # Try to parse JSON
                    try:
                        # Extract JSON from response
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                        elif "{" in content and "}" in content:
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            json_str = content[start:end]
                        else:
                            json_str = content
                        
                        result = json.loads(json_str)
                        print(f"✅ JSON Parsing Success: {result}")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON Parsing Failed: {e}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Analysis failed: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"❌ Analysis error: {e}")

async def main():
    print("🔧 Quick Fix for Gemini and Database Issues")
    print("=" * 50)
    
    # Fix 1: Database
    print("\n1. Fixing Database Schema...")
    fix_database()
    
    # Fix 2: Test Gemini Models
    print("\n2. Testing Gemini Models...")
    working_model = await test_gemini_api()
    
    if working_model:
        print(f"\n✅ Working Gemini Model: {working_model}")
        
        # Fix 3: Test Analysis
        print("\n3. Testing Trend Analysis...")
        await test_trend_analysis()
        
        # Generate fixed code
        print(f"\n4. Code Fix:")
        print(f"Replace this line in real_integration_main.py:")
        print(f'   url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={{self.gemini_api_key}}"')
        print(f"With:")
        print(f'   url = f"https://generativelanguage.googleapis.com/v1beta/models/{working_model}:generateContent?key={{self.gemini_api_key}}"')
        
    else:
        print("\n❌ No working Gemini models found")
        print("Will use Smart Analysis only")

if __name__ == "__main__":
    asyncio.run(main())