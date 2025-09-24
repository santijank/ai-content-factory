
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
