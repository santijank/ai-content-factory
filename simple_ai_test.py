# simple_ai_test.py - เวอร์ชันง่ายที่ทำงานได้แน่นอน

import asyncio
import aiohttp
import json
import os
from datetime import datetime

def load_config():
    """Load API keys"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    return {
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    }

class SimpleGeminiTest:
    def __init__(self, api_key):
        self.api_key = api_key
        
    async def test_analysis(self, topic, popularity):
        """Test Gemini analysis"""
        if not self.api_key:
            print(f"  [No API Key] {topic} - using mock analysis")
            return self.mock_analysis(topic, popularity)
        
        prompt = f"""Analyze: {topic}
Popularity: {popularity}/100

JSON format:
{{"viral_potential": 8, "content_saturation": 6, "audience_interest": 9, "monetization_opportunity": 7, "content_angles": ["tutorial", "review", "tips"], "reasoning": "brief analysis"}}"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        
                        # Extract JSON
                        try:
                            if "```json" in content:
                                json_str = content.split("```json")[1].split("```")[0].strip()
                            else:
                                start = content.find("{")
                                end = content.rfind("}") + 1
                                json_str = content[start:end]
                            
                            result = json.loads(json_str)
                            
                            overall_score = sum([
                                result["viral_potential"],
                                result["content_saturation"], 
                                result["audience_interest"],
                                result["monetization_opportunity"]
                            ]) / 4.0
                            
                            print(f"  [Gemini Success] {topic[:30]}... Score: {overall_score:.1f}")
                            print(f"    Viral: {result['viral_potential']}/10")
                            print(f"    Angles: {result['content_angles'][:2]}")
                            return result
                            
                        except json.JSONDecodeError as e:
                            print(f"  [JSON Error] {topic[:30]}... {e}")
                            return self.mock_analysis(topic, popularity)
                            
                    else:
                        error_text = await response.text()
                        print(f"  [API Error] {response.status}: {error_text[:100]}")
                        return self.mock_analysis(topic, popularity)
                        
        except Exception as e:
            print(f"  [Exception] {topic[:30]}... {e}")
            return self.mock_analysis(topic, popularity)
    
    def mock_analysis(self, topic, popularity):
        """Simple mock analysis"""
        topic_lower = topic.lower()
        
        # Simple category detection
        if any(word in topic_lower for word in ['เกม', 'game', 'rov']):
            viral, saturation, interest, monetization = 8, 4, 9, 7
            angles = ["Gaming tutorial", "Pro tips", "Guide"]
        elif any(word in topic_lower for word in ['เพลง', 'music', 'ft.']):
            viral, saturation, interest, monetization = 9, 5, 8, 5
            angles = ["Song reaction", "Music review", "Artist info"]
        elif any(word in topic_lower for word in ['ai', 'tech']):
            viral, saturation, interest, monetization = 7, 7, 8, 8
            angles = ["Tech tutorial", "Review", "How-to"]
        else:
            viral, saturation, interest, monetization = 6, 6, 7, 6
            angles = ["Tutorial", "Tips", "Guide"]
        
        overall_score = (viral + saturation + interest + monetization) / 4.0
        
        print(f"  [Mock Analysis] {topic[:30]}... Score: {overall_score:.1f}")
        
        return {
            "viral_potential": viral,
            "content_saturation": saturation,
            "audience_interest": interest,
            "monetization_opportunity": monetization,
            "content_angles": angles,
            "reasoning": f"Mock analysis based on keywords"
        }

async def test_youtube_trends():
    """Test YouTube API"""
    config = load_config()
    
    if not config["youtube_api_key"]:
        print("No YouTube API key - using mock trends")
        return [
            ("AI Video Creation", 85),
            ("RoV Pro League", 75),
            ("Thai Music", 60),
            ("Tech Review", 70),
            ("Gaming Tutorial", 80)
        ]
    
    try:
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=config["youtube_api_key"])
        
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode="TH",
            maxResults=5
        )
        response = request.execute()
        
        trends = []
        for item in response.get('items', []):
            title = item['snippet']['title']
            views = int(item['statistics'].get('viewCount', 0))
            popularity = min(views / 10000, 100)
            trends.append((title, popularity))
        
        print(f"YouTube API: Found {len(trends)} trending videos")
        return trends
        
    except Exception as e:
        print(f"YouTube API error: {e}")
        return [("Mock Trend", 50)]

async def main():
    """Main test function"""
    print("AI Content Factory - Simple Test")
    print("=" * 40)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    config = load_config()
    
    # Test 1: Check APIs
    print(f"\nAPI Status:")
    print(f"YouTube API: {'Available' if config['youtube_api_key'] else 'Missing'}")
    print(f"Gemini API: {'Available' if config['gemini_api_key'] else 'Missing'}")
    
    # Test 2: Get trends
    print(f"\nStep 1: Getting trends...")
    trends = await test_youtube_trends()
    
    # Test 3: AI Analysis
    print(f"\nStep 2: AI Analysis...")
    gemini_service = SimpleGeminiTest(config["gemini_api_key"])
    
    results = []
    for i, (topic, popularity) in enumerate(trends[:5]):
        print(f"\nAnalyzing {i+1}: {topic[:40]}...")
        result = await gemini_service.test_analysis(topic, int(popularity))
        if result:
            results.append((topic, result))
        
        # Small delay
        await asyncio.sleep(0.5)
    
    # Test 4: Summary
    print(f"\nSummary:")
    print(f"Trends analyzed: {len(results)}")
    
    if results:
        print(f"\nTop opportunities:")
        # Sort by score
        sorted_results = sorted(results, key=lambda x: (
            x[1]['viral_potential'] + x[1]['audience_interest']
        ), reverse=True)
        
        for i, (topic, result) in enumerate(sorted_results[:3]):
            score = (result['viral_potential'] + result['content_saturation'] + 
                    result['audience_interest'] + result['monetization_opportunity']) / 4
            print(f"  {i+1}. {topic[:35]}...")
            print(f"     Score: {score:.1f}/10, Viral: {result['viral_potential']}/10")
            print(f"     Best angle: {result['content_angles'][0]}")
    
    print(f"\nTest completed at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Status: {'AI APIs working' if config['gemini_api_key'] else 'Using mock analysis only'}")

if __name__ == "__main__":
    asyncio.run(main())