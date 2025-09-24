# main.py - อัพเดตเวอร์ชันที่แข็งแกร่งกว่า
from flask import Flask, render_template, request, jsonify
import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# เพิ่ม paths
sys.path.append('content-engine')
sys.path.append('database')

app = Flask(__name__)

# Global variables
groq_service = None
ai_service_status = {
    'groq': False,
    'openai': False,
    'working_model': None
}

def initialize_ai_services():
    """เริ่มต้น AI services และตรวจสอบสถานะ"""
    global groq_service, ai_service_status
    
    print("🤖 เริ่มต้น AI Services...")
    
    # ทดสอบ Groq
    try:
        from ai_services.text_ai.groq_service import GroqService
        groq_service = GroqService()
        
        # ทดสอบว่าใช้ได้ไหม
        if hasattr(groq_service, 'test_model') and groq_service.test_model():
            ai_service_status['groq'] = True
            ai_service_status['working_model'] = groq_service.model
            print(f"✅ Groq ready with model: {groq_service.model}")
        else:
            print("⚠️ Groq available but no working models")
            
    except Exception as e:
        print(f"❌ Groq initialization error: {e}")
        groq_service = None
    
    # ทดสอบ OpenAI
    try:
        import openai
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # ทดสอบง่ายๆ
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        ai_service_status['openai'] = True
        print("✅ OpenAI ready")
        
    except Exception as e:
        if "insufficient_quota" in str(e):
            print("⚠️ OpenAI quota exceeded")
        else:
            print(f"❌ OpenAI error: {e}")
        ai_service_status['openai'] = False

# เริ่มต้น AI services เมื่อ start app
initialize_ai_services()

@app.route('/')
def dashboard():
    """Dashboard หลัก"""
    return render_template('dashboard.html')

@app.route('/api/system-status')
def system_status():
    """ตรวจสอบสถานะระบบ"""
    return jsonify({
        'ai_services': ai_service_status,
        'api_keys_configured': {
            'groq': bool(os.getenv('GROQ_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY'))
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/collect-trends', methods=['POST'])
def collect_trends():
    """เก็บ trends และวิเคราะห์ด้วย AI"""
    try:
        print("🔄 เริ่มเก็บ trends...")
        
        # Mock trends data (จะเปลี่ยนเป็น real API ภายหลัง)
        trends = [
            {
                'topic': 'AI Content Creation 2024',
                'popularity_score': 89,
                'growth_rate': 25,
                'source': 'youtube'
            },
            {
                'topic': 'TikTok Marketing Trends',
                'popularity_score': 76,
                'growth_rate': 18,
                'source': 'google_trends'
            },
            {
                'topic': 'Passive Income Ideas',
                'popularity_score': 82,
                'growth_rate': 32,
                'source': 'youtube'
            },
            {
                'topic': 'Social Media Analytics',
                'popularity_score': 71,
                'growth_rate': 15,
                'source': 'twitter'
            },
            {
                'topic': 'Video Editing Tutorial',
                'popularity_score': 68,
                'growth_rate': 22,
                'source': 'youtube'
            }
        ]
        
        # วิเคราะห์แต่ละ trend
        analyzed_trends = []
        ai_analysis_count = 0
        
        for trend in trends:
            if groq_service and ai_service_status['groq']:
                try:
                    print(f"🤖 AI วิเคราะห์: {trend['topic']}")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    analysis = loop.run_until_complete(
                        groq_service.analyze_trend(trend)
                    )
                    loop.close()
                    
                    trend['ai_analysis'] = analysis
                    trend['analysis_method'] = 'ai'
                    ai_analysis_count += 1
                    
                except Exception as e:
                    print(f"❌ AI analysis failed for {trend['topic']}: {e}")
                    trend['ai_analysis'] = get_fallback_analysis(trend)
                    trend['analysis_method'] = 'fallback'
            else:
                # ใช้ rule-based analysis
                trend['ai_analysis'] = get_smart_fallback_analysis(trend)
                trend['analysis_method'] = 'rule_based'
            
            # คำนวณ opportunity score
            scores = trend['ai_analysis']['scores']
            opportunity_score = (
                scores.get('viral_potential', 5) * 0.3 +
                scores.get('audience_interest', 5) * 0.3 +
                scores.get('monetization_opportunity', 5) * 0.2 +
                (10 - scores.get('content_saturation', 5)) * 0.2
            )
            trend['opportunity_score'] = round(opportunity_score, 1)
            analyzed_trends.append(trend)
        
        # เรียงลำดับตาม opportunity score
        analyzed_trends.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'trends_collected': len(analyzed_trends),
            'ai_analysis_count': ai_analysis_count,
            'trends': analyzed_trends,
            'ai_enabled': ai_service_status['groq'] or ai_service_status['openai'],
            'working_model': ai_service_status.get('working_model'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error collecting trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """สร้างเนื้อหาจาก opportunity ที่เลือก"""
    try:
        data = request.json
        idea = data.get('idea', '')
        platform = data.get('platform', 'youtube')
        
        if not idea:
            return jsonify({'success': False, 'error': 'Missing content idea'})
        
        print(f"🎬 กำลังสร้างเนื้อหา: {idea}")
        
        if groq_service and ai_service_status['groq']:
            try:
                # สร้าง script ด้วย AI จริง
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                content = loop.run_until_complete(
                    groq_service.generate_content_script(idea, platform)
                )
                loop.close()
                
                content['generation_method'] = 'ai'
                content['model_used'] = ai_service_status.get('working_model', 'unknown')
                
            except Exception as e:
                print(f"❌ AI content generation failed: {e}")
                content = get_fallback_content(idea, platform)
                content['generation_method'] = 'fallback'
        else:
            # Fallback content with smart templates
            content = get_smart_fallback_content(idea, platform)
            content['generation_method'] = 'template'
        
        return jsonify({
            'success': True,
            'content': content,
            'ai_enabled': content['generation_method'] == 'ai',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Content generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_fallback_analysis(trend_data):
    """ข้อมูล fallback พื้นฐาน"""
    return {
        "scores": {
            "viral_potential": 5, 
            "content_saturation": 5, 
            "audience_interest": 5, 
            "monetization_opportunity": 5
        },
        "content_angles": [
            "มุมมองทั่วไป", 
            "วิธีการใหม่", 
            "เคล็ดลับที่มีประโยชน์"
        ],
        "recommended_platforms": ["youtube"],
        "estimated_reach": 10000
    }

def get_smart_fallback_analysis(trend_data):
    """Rule-based analysis ที่ชาญฉลาดกว่า"""
    topic = trend_data.get('topic', '').lower()
    popularity = trend_data.get('popularity_score', 50)
    growth = trend_data.get('growth_rate', 10)
    
    # คำนวณคะแนนตาม keywords และ metrics
    viral_potential = min(10, max(1, int(popularity / 10)))
    audience_interest = min(10, max(1, int((popularity + growth) / 15)))
    
    # ตรวจสอบ keywords สำหรับการประเมิน
    high_engagement_keywords = ['tutorial', 'how to', 'tips', 'secrets', 'viral', 'trending']
    monetization_keywords = ['business', 'money', 'income', 'marketing', 'sales']
    saturated_keywords = ['basic', 'simple', 'easy', 'beginner']
    
    content_saturation = 5
    monetization_opportunity = 5
    
    for keyword in high_engagement_keywords:
        if keyword in topic:
            viral_potential = min(10, viral_potential + 1)
            break
    
    for keyword in monetization_keywords:
        if keyword in topic:
            monetization_opportunity = min(10, monetization_opportunity + 2)
            break
    
    for keyword in saturated_keywords:
        if keyword in topic:
            content_saturation = min(10, content_saturation + 2)
            break
    
    # สร้าง content angles แบบชาญฉลาด
    if 'tutorial' in topic or 'how to' in topic:
        angles = [
            "สอนแบบขั้นตอนง่ายๆ",
            "เคล็ดลับเพิ่มเติมที่คนไม่รู้", 
            "ข้อผิดพลาดที่ควรหลีกเลี่ยง"
        ]
    elif 'marketing' in topic or 'business' in topic:
        angles = [
            "กลยุทธ์ที่ใช้ได้จริง",
            "ตัวอย่าง case study", 
            "เทคนิคของผู้เชี่ยวชาญ"
        ]
    else:
        angles = [
            f"มุมมองใหม่ของ {trend_data.get('topic', 'หัวข้อ')}",
            "เทรนด์ที่กำลังมาแรง", 
            "วิธีการที่คนไม่เคยรู้"
        ]
    
    return {
        "scores": {
            "viral_potential": viral_potential,
            "content_saturation": content_saturation,
            "audience_interest": audience_interest,
            "monetization_opportunity": monetization_opportunity
        },
        "content_angles": angles,
        "recommended_platforms": ["youtube", "tiktok"] if viral_potential > 6 else ["youtube"],
        "estimated_reach": popularity * growth * 10
    }

def get_fallback_content(idea, platform):
    """Fallback content พื้นฐาน"""
    return {
        "title": f"เนื้อหาเกี่ยวกับ {idea}",
        "description": "เนื้อหาที่น่าสนใจและมีประโยชน์",
        "script": {
            "hook": "สวัสดีครับ! วันนี้เรามาเรียนรู้เรื่องใหม่กัน",
            "main_content": f"เรื่อง {idea} นั้นสำคัญเพราะ...",
            "cta": "ถ้าชอบก็กด Like และ Subscribe นะครับ"
        },
        "hashtags": ["#content", "#viral"],
        "estimated_duration": "2-3 นาที"
    }

def get_smart_fallback_content(idea, platform):
    """Template-based content ที่ชาญฉลาดกว่า"""
    idea_lower = idea.lower()
    
    # เลือก template ตาม keyword
    if any(word in idea_lower for word in ['tutorial', 'how to', 'วิธี', 'สอน']):
        template_type = 'tutorial'
    elif any(word in idea_lower for word in ['tips', 'เคล็ดลับ', 'ความลับ']):
        template_type = 'tips'
    elif any(word in idea_lower for word in ['review', 'รีวิว', 'ทดสอบ']):
        template_type = 'review'
    else:
        template_type = 'general'
    
    templates = {
        'tutorial': {
            "title": f"สอน {idea} แบบละเอียด | เริ่มต้นจากศูนย์",
            "hook": "ใครที่อยากเรียนรู้เรื่องนี้ต้องดู! วันนี้เราจะสอนตั้งแต่เริ่มต้น",
            "main": f"เรื่อง {idea} นั้นทำได้ง่ายมาก ขั้นตอนแรก... ขั้นตอนที่สอง... และสุดท้าย...",
            "hashtags": ["#tutorial", "#howto", "#เรียนฟรี"]
        },
        'tips': {
            "title": f"5 เคล็ดลับ {idea} ที่คนไม่เคยรู้!",
            "hook": "เคล็ดลับที่จะเปลี่ยนชีวิตคุณ! ข้อแรกนี้คนไม่เคยคิด",
            "main": f"เคล็ดลับแรกของ {idea} คือ... เคล็ดลับที่สองสำคัญมาก... และเคล็ดลับสุดท้าย...",
            "hashtags": ["#tips", "#เคล็ดลับ", "#lifehack"]
        },
        'review': {
            "title": f"รีวิว {idea} จริงไหม? ทดสอบแล้วผลออกมา...",
            "hook": "คนเขาพูดกันเรื่องนี้ เราเลยไปทดสอบจริงมา ผลออกมา...",
            "main": f"การทดสอบ {idea} ครั้งนี้ พบว่า... ข้อดีคือ... ข้อเสียคือ...",
            "hashtags": ["#review", "#รีวิว", "#ทดสอบจริง"]
        },
        'general': {
            "title": f"ทุกอย่างเกี่ยวกับ {idea} ที่คุณต้องรู้",
            "hook": "เรื่องที่ทุกคนสงสัย วันนี้เรามีคำตอบแล้ว!",
            "main": f"เรื่อง {idea} นั้น มีหลายด้านที่น่าสนใจ อย่างแรก... อย่างที่สอง...",
            "hashtags": ["#ความรู้", "#น่าสนใจ", "#viral"]
        }
    }
    
    template = templates[template_type]
    
    # ปรับ CTA ตาม platform
    if platform == 'tiktok':
        cta = "ถ้าชอบก็ double tap และ follow เลย! 💖"
    elif platform == 'youtube':
        cta = "ถ้าชอบกด Like และ Subscribe กดกระดิ่งด้วยนะครับ! 🔔"
    else:
        cta = "ถ้าชอบก็ให้กำลังใจกันด้วยนะ! 👍"
    
    return {
        "title": template["title"],
        "description": f"เนื้อหาคุณภาพเกี่ยวกับ {idea} ที่คุณไม่ควรพลาด",
        "script": {
            "hook": template["hook"],
            "main_content": template["main"],
            "cta": cta
        },
        "hashtags": template["hashtags"] + [f"#{idea.replace(' ', '')}"],
        "estimated_duration": "2-3 นาที"
    }

@app.route('/api/reinitialize-ai', methods=['POST'])
def reinitialize_ai():
    """ลองเริ่ม AI services ใหม่"""
    try:
        initialize_ai_services()
        return jsonify({
            'success': True,
            'ai_services': ai_service_status,
            'message': 'AI services reinitialized'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 เริ่มต้น AI Content Factory")
    print(f"🤖 AI Status: Groq={ai_service_status['groq']}, OpenAI={ai_service_status['openai']}")
    if ai_service_status['working_model']:
        print(f"✨ Using model: {ai_service_status['working_model']}")
    print("🔗 URL: http://localhost:5000")
    print("📝 กด Ctrl+C เพื่อหยุด")
    
    app.run(debug=True, port=5000)