
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
