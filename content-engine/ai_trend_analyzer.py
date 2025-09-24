import os
import json
import sys
from datetime import datetime

# เพิ่ม path เพื่อ import จาก database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AITrendAnalyzer:
    def __init__(self, ai_service='mock'):
        self.ai_service = ai_service
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
    def analyze_trend_potential(self, trend_data):
        """วิเคราะห์ศักยภาพของ trend สำหรับสร้าง content"""
        if self.ai_service == 'groq' and self.groq_api_key:
            return self.analyze_with_groq(trend_data)
        else:
            return self.analyze_with_mock(trend_data)
    
    def analyze_with_groq(self, trend_data):
        """วิเคราะห์ด้วย Groq AI"""
        try:
            import requests
            
            prompt = self.create_analysis_prompt(trend_data)
            
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'mixtral-8x7b-32768',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert content strategist analyzing trends for content creation opportunities.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1000
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['choices'][0]['message']['content']
                return self.parse_ai_analysis(analysis_text, trend_data)
            else:
                print(f"❌ Groq API error: {response.status_code}")
                return self.analyze_with_mock(trend_data)
                
        except Exception as e:
            print(f"❌ Error with Groq analysis: {e}")
            return self.analyze_with_mock(trend_data)
    
    def analyze_with_mock(self, trend_data):
        """วิเคราะห์ด้วย logic แบบง่าย (สำหรับทดสอบ)"""
        # คำนวณคะแนนต่างๆ ตาม logic แบบง่าย
        viral_potential = self.calculate_viral_potential(trend_data)
        content_saturation = self.calculate_content_saturation(trend_data)
        audience_interest = self.calculate_audience_interest(trend_data)
        monetization_opportunity = self.calculate_monetization_opportunity(trend_data)
        
        # สร้าง content angles
        content_angles = self.generate_content_angles(trend_data)
        
        analysis = {
            'trend_id': trend_data.get('id'),
            'trend_topic': trend_data['topic'],
            'scores': {
                'viral_potential': viral_potential,
                'content_saturation': content_saturation,
                'audience_interest': audience_interest,
                'monetization_opportunity': monetization_opportunity,
                'overall_score': (viral_potential + audience_interest + monetization_opportunity - content_saturation) / 3
            },
            'content_angles': content_angles,
            'recommendations': self.generate_recommendations(viral_potential, content_saturation, audience_interest, monetization_opportunity),
            'estimated_metrics': {
                'potential_views': self.estimate_views(trend_data),
                'competition_level': self.assess_competition(trend_data),
                'production_difficulty': self.assess_production_difficulty(trend_data)
            },
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        print(f"✅ Analyzed trend: {trend_data['topic']} (Score: {analysis['scores']['overall_score']:.1f})")
        return analysis
    
    def create_analysis_prompt(self, trend_data):
        """สร้าง prompt สำหรับ AI"""
        return f"""
        Analyze this trending topic for content creation opportunities:
        
        Topic: {trend_data['topic']}
        Source: {trend_data['source']}
        Current popularity: {trend_data['popularity_score']}
        Growth rate: {trend_data['growth_rate']}%
        Keywords: {', '.join(trend_data.get('keywords', []))}
        Category: {trend_data.get('category', 'General')}
        
        Please rate each aspect from 1-10 and provide analysis:
        
        1. Viral Potential: How likely is this to go viral?
        2. Content Saturation: How much competition exists?
        3. Audience Interest: How engaged is the audience?
        4. Monetization Opportunity: How profitable could this be?
        
        Also suggest 3 unique content angles and provide recommendations.
        
        Format your response as JSON with these keys:
        - viral_potential (1-10)
        - content_saturation (1-10, higher = more saturated)
        - audience_interest (1-10)
        - monetization_opportunity (1-10)
        - content_angles (array of 3 strings)
        - recommendations (string)
        """
    
    def parse_ai_analysis(self, analysis_text, trend_data):
        """แปลงผลลัพธ์จาก AI เป็น structured data"""
        try:
            # ลองแปลง JSON ถ้า AI ส่งมาในรูปแบบ JSON
            analysis_json = json.loads(analysis_text)
            
            return {
                'trend_id': trend_data.get('id'),
                'trend_topic': trend_data['topic'],
                'scores': {
                    'viral_potential': analysis_json.get('viral_potential', 5),
                    'content_saturation': analysis_json.get('content_saturation', 5),
                    'audience_interest': analysis_json.get('audience_interest', 5),
                    'monetization_opportunity': analysis_json.get('monetization_opportunity', 5),
                    'overall_score': (
                        analysis_json.get('viral_potential', 5) + 
                        analysis_json.get('audience_interest', 5) + 
                        analysis_json.get('monetization_opportunity', 5) - 
                        analysis_json.get('content_saturation', 5)
                    ) / 3
                },
                'content_angles': analysis_json.get('content_angles', []),
                'recommendations': analysis_json.get('recommendations', ''),
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except json.JSONDecodeError:
            # ถ้าไม่ใช่ JSON ให้ใช้ mock analysis
            return self.analyze_with_mock(trend_data)
    
    def calculate_viral_potential(self, trend_data):
        """คำนวณศักยภาพการแพร่กระจาย"""
        score = 5  # base score
        
        # ปรับตามความนิยม
        if trend_data['popularity_score'] > 80:
            score += 2
        elif trend_data['popularity_score'] > 60:
            score += 1
        
        # ปรับตาม growth rate
        if trend_data['growth_rate'] > 20:
            score += 2
        elif trend_data['growth_rate'] > 10:
            score += 1
        
        # ปรับตาม keywords
        viral_keywords = ['ai', 'tutorial', 'hack', 'secret', 'amazing', 'new']
        keyword_matches = sum(1 for kw in trend_data.get('keywords', []) 
                             if any(viral in kw.lower() for viral in viral_keywords))
        score += min(keyword_matches, 2)
        
        return min(score, 10)
    
    def calculate_content_saturation(self, trend_data):
        """คำนวณระดับการอิ่มตัวของเนื้อหา"""
        # ตัวอย่างการคำนวณแบบง่าย
        # ในอนาคตอาจใช้ API เพื่อเช็คจำนวน content ที่มีอยู่
        
        base_saturation = 5
        
        # หัวข้อที่นิยมมักจะอิ่มตัวมากกว่า
        popular_topics = ['tutorial', 'review', 'unboxing']
        if any(topic in trend_data['topic'].lower() for topic in popular_topics):
            base_saturation += 2
        
        # Source ที่มี competition สูง
        if trend_data['source'] == 'youtube':
            base_saturation += 1
        
        return min(base_saturation, 10)
    
    def calculate_audience_interest(self, trend_data):
        """คำนวณความสนใจของผู้ชม"""
        score = trend_data['popularity_score'] / 10  # แปลงจาก 0-100 เป็น 0-10
        
        # ปรับตาม raw data
        raw_data = trend_data.get('raw_data', {})
        if 'likes' in raw_data and 'views' in raw_data:
            if raw_data['views'] > 0:
                engagement_rate = raw_data['likes'] / raw_data['views']
                if engagement_rate > 0.05:  # 5% engagement ดี
                    score += 1
        
        return min(score, 10)
    
    def calculate_monetization_opportunity(self, trend_data):
        """คำนวณโอกาสในการสร้างรายได้"""
        score = 5  # base score
        
        # หมวดหมู่ที่สร้างรายได้ได้ดี
        profitable_categories = ['technology', 'business', 'education', 'finance']
        if trend_data.get('category', '').lower() in profitable_categories:
            score += 2
        
        # keywords ที่เกี่ยวกับการซื้อขาย
        commercial_keywords = ['buy', 'review', 'best', 'comparison', 'guide']
        keyword_matches = sum(1 for kw in trend_data.get('keywords', []) 
                             if any(commercial in kw.lower() for commercial in commercial_keywords))
        score += min(keyword_matches, 2)
        
        return min(score, 10)
    
    def generate_content_angles(self, trend_data):
        """สร้างมุมมองการสร้างเนื้อหา"""
        topic = trend_data['topic']
        keywords = trend_data.get('keywords', [])
        
        angles = [
            f"สอนวิธีใช้ {topic} แบบง่ายๆ สำหรับมือใหม่",
            f"เปรียบเทียบ {topic} กับทางเลือกอื่นๆ",
            f"เคล็ดลับและเทคนิคขั้นสูงสำหรับ {topic}"
        ]
        
        # เพิ่มมุมมองตาม keywords
        if keywords:
            angles.append(f"ทำไม {keywords[0]} ถึงสำคัญในยุค {topic}")
        
        return angles[:3]
    
    def generate_recommendations(self, viral_potential, content_saturation, audience_interest, monetization_opportunity):
        """สร้างคำแนะนำ"""
        recommendations = []
        
        if viral_potential > 7:
            recommendations.append("มีศักยภาพไวรัลสูง ควรสร้างเนื้อหาเร็วๆ")
        
        if content_saturation > 7:
            recommendations.append("ตลาดอิ่มตัว ต้องหามุมมองใหม่ๆ")
        elif content_saturation < 4:
            recommendations.append("โอกาสดี มี competition น้อย")
        
        if audience_interest > 7:
            recommendations.append("ผู้ชมสนใจสูง เหมาะทำ series")
        
        if monetization_opportunity > 7:
            recommendations.append("โอกาสสร้างรายได้ดี ควร focus ที่ quality")
        
        return " | ".join(recommendations) if recommendations else "แนวโน้มปกติ ดำเนินการตามแผน"
    
    def estimate_views(self, trend_data):
        """ประเมินจำนวน views ที่คาดหวัง"""
        base_views = trend_data['popularity_score'] * 1000
        
        if trend_data['growth_rate'] > 20:
            base_views *= 1.5
        
        return int(base_views)
    
    def assess_competition(self, trend_data):
        """ประเมินระดับการแข่งขัน"""
        if trend_data['popularity_score'] > 80:
            return 'high'
        elif trend_data['popularity_score'] > 50:
            return 'medium'
        else:
            return 'low'
    
    def assess_production_difficulty(self, trend_data):
        """ประเมินความยากในการผลิต"""
        complex_topics = ['programming', 'finance', 'science']
        
        if any(topic in trend_data['topic'].lower() for topic in complex_topics):
            return 'high'
        elif 'tutorial' in trend_data['topic'].lower():
            return 'medium'
        else:
            return 'low'

class OpportunityGenerator:
    def __init__(self, db):
        self.db = db
        self.analyzer = AITrendAnalyzer()
    
    def generate_content_opportunities(self, min_score=6.0):
        """สร้าง content opportunities จาก trends"""
        try:
            from database.models_simple import TrendModel, ContentOpportunityModel
            
            trend_model = TrendModel(self.db)
            opportunity_model = ContentOpportunityModel(self.db)
            
            # ดึง trends ล่าสุด
            trends = trend_model.get_all()
            opportunities_created = 0
            
            print(f"🔍 Analyzing {len(trends)} trends for content opportunities...")
            
            for trend in trends:
                # วิเคราะห์ trend
                analysis = self.analyzer.analyze_trend_potential(trend)
                
                # สร้าง opportunities หากคะแนนผ่านเกณฑ์
                if analysis['scores']['overall_score'] >= min_score:
                    for angle in analysis['content_angles']:
                        opportunity_id = opportunity_model.create(
                            trend_id=trend['id'],
                            suggested_angle=angle,
                            estimated_views=analysis['estimated_metrics']['potential_views'],
                            competition_level=analysis['estimated_metrics']['competition_level'],
                            priority_score=analysis['scores']['overall_score'],
                            production_cost=self.estimate_production_cost(analysis),
                            estimated_roi=self.estimate_roi(analysis)
                        )
                        
                        if opportunity_id:
                            opportunities_created += 1
            
            print(f"✅ Created {opportunities_created} content opportunities")
            return opportunities_created
            
        except Exception as e:
            print(f"❌ Error generating opportunities: {e}")
            return 0
    
    def estimate_production_cost(self, analysis):
        """ประเมินต้นทุนการผลิต"""
        difficulty = analysis['estimated_metrics']['production_difficulty']
        
        cost_map = {
            'low': 50,     # บาท
            'medium': 150, # บาท
            'high': 300    # บาท
        }
        
        return cost_map.get(difficulty, 100)
    
    def estimate_roi(self, analysis):
        """ประเมิน ROI"""
        potential_views = analysis['estimated_metrics']['potential_views']
        monetization_score = analysis['scores']['monetization_opportunity']
        
        # สูตรคร่าวๆ: views * monetization_score * 0.001
        estimated_revenue = potential_views * monetization_score * 0.001
        estimated_cost = self.estimate_production_cost(analysis)
        
        if estimated_cost > 0:
            roi = (estimated_revenue - estimated_cost) / estimated_cost
            return max(roi, 0)  # ไม่ให้ติดลบ
        
        return 0

def main():
    """ทดสอบ AI Trend Analyzer"""
    print("🤖 Testing AI Trend Analyzer...")
    
    try:
        # สร้าง database connection
        from database.models_simple import Database
        db = Database()
        
        # สร้าง opportunity generator
        generator = OpportunityGenerator(db)
        
        # สร้าง opportunities
        opportunities_count = generator.generate_content_opportunities(min_score=5.0)
        
        if opportunities_count > 0:
            # ดึง opportunities ที่สร้างมา
            from database.models_simple import ContentOpportunityModel
            opportunity_model = ContentOpportunityModel(db)
            
            opportunities = opportunity_model.get_by_status('pending')
            
            print(f"\n📋 Top Content Opportunities:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"{i}. {opp['suggested_angle']}")
                print(f"   Priority: {opp['priority_score']:.1f} | ROI: {opp['estimated_roi']:.2f}")
                print(f"   Views: {opp['estimated_views']} | Cost: ฿{opp['production_cost']}")
                print()
            
            return True
        else:
            print("⚠️ No opportunities created. Try running trend collection first.")
            return False
            
    except Exception as e:
        print(f"❌ AI Trend Analyzer test failed: {e}")
        return False

if __name__ == "__main__":
    main()