# content-engine/services/visual_generator.py
import asyncio
import json
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import requests
import io
import base64
import google.generativeai as genai

@dataclass
class VisualPlan:
    scenes: List[Dict]
    thumbnail_design: Dict
    color_scheme: Dict
    text_overlays: List[Dict]
    b_roll_suggestions: List[str]

@dataclass
class ThumbnailDesign:
    background_image: str
    title_text: str
    subtitle_text: str
    color_scheme: Dict
    layout_type: str
    elements: List[Dict]

class ThumbnailGenerator:
    """สร้าง thumbnail อัตโนมัติ"""
    
    def __init__(self):
        self.canvas_sizes = {
            "youtube": (1280, 720),
            "tiktok": (1080, 1920),
            "instagram": (1080, 1080),
            "facebook": (1200, 630)
        }
        
        # Color schemes สำหรับเนื้อหาประเภทต่างๆ
        self.color_schemes = {
            "tech": {"primary": "#00D4FF", "secondary": "#1A1A2E", "accent": "#16213E"},
            "gaming": {"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#45B7D1"},
            "educational": {"primary": "#96CEB4", "secondary": "#FFEAA7", "accent": "#DDA0DD"},
            "entertainment": {"primary": "#FF7675", "secondary": "#FDCB6E", "accent": "#6C5CE7"},
            "business": {"primary": "#0984E3", "secondary": "#00B894", "accent": "#2D3436"}
        }

    async def generate_thumbnail(self, 
                               title: str,
                               content_type: str,
                               platform: str = "youtube",
                               style: str = "modern") -> Dict:
        """สร้าง thumbnail พร้อมหลายตัวเลือก"""
        
        canvas_size = self.canvas_sizes.get(platform, self.canvas_sizes["youtube"])
        color_scheme = self.color_schemes.get(content_type, self.color_schemes["entertainment"])
        
        designs = []
        
        # สร้าง 3 ตัวเลือก design
        for i, layout in enumerate(["centered", "left_text", "dynamic"]):
            design = await self._create_thumbnail_design(
                title, canvas_size, color_scheme, layout, i
            )
            designs.append(design)
        
        return {
            "designs": designs,
            "recommended": designs[0],  # แนะนำตัวแรก
            "canvas_size": canvas_size,
            "color_scheme": color_scheme
        }

    async def _create_thumbnail_design(self, 
                                     title: str,
                                     canvas_size: Tuple[int, int],
                                     color_scheme: Dict,
                                     layout: str,
                                     variant: int) -> ThumbnailDesign:
        """สร้างการออกแบบ thumbnail แต่ละแบบ"""
        
        # สร้าง background gradient
        background = self._create_gradient_background(canvas_size, color_scheme)
        
        # คำนวณตำแหน่งข้อความ
        text_layout = self._calculate_text_layout(canvas_size, layout)
        
        # สร้าง elements ที่จะใส่
        elements = self._generate_design_elements(title, color_scheme, variant)
        
        return ThumbnailDesign(
            background_image=background,
            title_text=title,
            subtitle_text="",
            color_scheme=color_scheme,
            layout_type=layout,
            elements=elements
        )

    def _create_gradient_background(self, canvas_size: Tuple[int, int], color_scheme: Dict) -> str:
        """สร้าง background แบบ gradient"""
        
        width, height = canvas_size
        image = Image.new('RGB', canvas_size, color=color_scheme["secondary"])
        
        # สร้าง gradient effect
        draw = ImageDraw.Draw(image)
        
        for i in range(height):
            alpha = i / height
            # Interpolate between primary and secondary colors
            color = self._interpolate_color(
                color_scheme["primary"], 
                color_scheme["secondary"], 
                alpha
            )
            draw.line([(0, i), (width, i)], fill=color)
        
        # Convert to base64 for easy storage
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()

    def _interpolate_color(self, color1: str, color2: str, t: float) -> str:
        """ผสมสีระหว่าง color1 และ color2"""
        # Convert hex to RGB
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        # Interpolate
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def _calculate_text_layout(self, canvas_size: Tuple[int, int], layout: str) -> Dict:
        """คำนวณตำแหน่งข้อความ"""
        width, height = canvas_size
        
        layouts = {
            "centered": {
                "title_pos": (width//2, height//2),
                "title_align": "center",
                "max_width": width * 0.8
            },
            "left_text": {
                "title_pos": (width * 0.1, height * 0.3),
                "title_align": "left",
                "max_width": width * 0.6
            },
            "dynamic": {
                "title_pos": (width * 0.2, height * 0.4),
                "title_align": "left",
                "max_width": width * 0.7
            }
        }
        
        return layouts.get(layout, layouts["centered"])

    def _generate_design_elements(self, title: str, color_scheme: Dict, variant: int) -> List[Dict]:
        """สร้าง elements ตกแต่งเพิ่มเติม"""
        
        elements = []
        
        # เพิ่ม decorative elements ตาม variant
        if variant == 0:  # Simple and clean
            elements.append({
                "type": "rectangle",
                "color": color_scheme["accent"],
                "position": (50, 50),
                "size": (200, 10),
                "opacity": 0.8
            })
            
        elif variant == 1:  # Bold and dynamic
            elements.extend([
                {
                    "type": "circle",
                    "color": color_scheme["primary"],
                    "position": (100, 100),
                    "radius": 30,
                    "opacity": 0.6
                },
                {
                    "type": "triangle",
                    "color": color_scheme["accent"],
                    "position": (200, 150),
                    "size": 40,
                    "opacity": 0.7
                }
            ])
            
        elif variant == 2:  # Minimalist
            elements.append({
                "type": "line",
                "color": color_scheme["primary"],
                "start": (0, 200),
                "end": (300, 200),
                "width": 5,
                "opacity": 0.9
            })
        
        return elements

class VisualPlanner:
    """วางแผน visual elements สำหรับวิดีโอ"""
    
    def __init__(self):
        genai.configure(api_key="your-gemini-api-key")
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def create_visual_plan(self, script_components, content_type: str) -> VisualPlan:
        """สร้างแผน visual จาก script"""
        
        prompt = self._build_visual_prompt(script_components, content_type)
        
        try:
            response = await self._call_gemini_api(prompt)
            return self._parse_visual_response(response)
        except Exception as e:
            print(f"Error creating visual plan: {e}")
            return self._create_fallback_plan(script_components)

    def _build_visual_prompt(self, script, content_type: str) -> str:
        """สร้าง prompt สำหรับ visual planning"""
        
        return f"""วางแผน visual elements สำหรับวิดีโอประเภท {content_type}

Script:
Hook: {script.hook}
Introduction: {script.introduction}
Main Content: {script.main_content}
Conclusion: {script.conclusion}

กรุณาแนะนำในรูปแบบ JSON:
{{
    "scenes": [
        {{
            "timestamp": "0:00-0:05",
            "description": "แสดงอะไรในช่วงนี้",
            "visual_type": "talking_head/b_roll/graphics",
            "text_overlay": "ข้อความที่จะแสดง",
            "transition": "cut/fade/slide"
        }}
    ],
    "thumbnail_concept": {{
        "main_element": "สิ่งที่เป็นจุดเด่น",
        "background": "ประเภท background",
        "text_style": "สไตล์ข้อความ",
        "color_mood": "อารมณ์สี"
    }},
    "b_roll_suggestions": [
        "ฟุตเทจที่ควรมี 1",
        "ฟุตเทจที่ควรมี 2"
    ],
    "text_overlays": [
        {{
            "text": "ข้อความ",
            "timing": "0:30-0:35",
            "style": "bold/animated/simple"
        }}
    ]
}}"""

    async def _call_gemini_api(self, prompt: str) -> str:
        """เรียก Gemini API"""
        response = self.model.generate_content(prompt)
        return response.text

    def _parse_visual_response(self, response: str) -> VisualPlan:
        """แปลง response เป็น VisualPlan"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            return VisualPlan(
                scenes=data.get('scenes', []),
                thumbnail_design=data.get('thumbnail_concept', {}),
                color_scheme={"primary": "#FF6B6B", "secondary": "#4ECDC4"},
                text_overlays=data.get('text_overlays', []),
                b_roll_suggestions=data.get('b_roll_suggestions', [])
            )
        except Exception as e:
            print(f"Error parsing visual response: {e}")
            return self._create_fallback_plan(None)

    def _create_fallback_plan(self, script) -> VisualPlan:
        """สร้าง visual plan พื้นฐาน"""
        return VisualPlan(
            scenes=[
                {
                    "timestamp": "0:00-0:05",
                    "description": "Hook scene",
                    "visual_type": "talking_head",
                    "text_overlay": "",
                    "transition": "cut"
                },
                {
                    "timestamp": "0:05-1:00",
                    "description": "Main content",
                    "visual_type": "b_roll",
                    "text_overlay": "เนื้อหาหลัก",
                    "transition": "fade"
                }
            ],
            thumbnail_design={
                "main_element": "หัวข้อเรื่อง",
                "background": "gradient",
                "text_style": "bold",
                "color_mood": "energetic"
            },
            color_scheme={"primary": "#FF6B6B", "secondary": "#4ECDC4"},
            text_overlays=[],
            b_roll_suggestions=["stock footage", "screen recording"]
        )

class ImageAssetManager:
    """จัดการ image assets และ stock photos"""
    
    def __init__(self):
        self.stock_apis = {
            "unsplash": "https://api.unsplash.com/search/photos",
            "pexels": "https://api.pexels.com/v1/search"
        }

    async def find_relevant_images(self, keywords: List[str], count: int = 5) -> List[Dict]:
        """ค้นหารูปภาพที่เกี่ยวข้อง"""
        
        images = []
        
        for keyword in keywords:
            try:
                # ในระบบจริงจะเรียก stock photo APIs
                # ตอนนี้ return mock data
                mock_images = self._get_mock_images(keyword, count)
                images.extend(mock_images)
            except Exception as e:
                print(f"Error finding images for {keyword}: {e}")
        
        return images[:count]

    def _get_mock_images(self, keyword: str, count: int) -> List[Dict]:
        """สร้าง mock image data"""
        return [
            {
                "id": f"img_{keyword}_{i}",
                "url": f"https://picsum.photos/800/600?random={hash(keyword) + i}",
                "description": f"Image related to {keyword}",
                "tags": [keyword, "stock", "free"],
                "resolution": "800x600"
            }
            for i in range(count)
        ]

# Integration Example
async def main():
    """ตัวอย่างการใช้ระบบ visual generation"""
    
    # Mock script components
    from script_generator import ScriptComponents
    
    script = ScriptComponents(
        hook="AI กำลังเปลี่ยนโลก!",
        introduction="วันนี้เราจะมาดู AI ที่ใหม่ล่าสุด",
        main_content="AI สามารถทำอะไรได้บ้าง...",
        conclusion="สรุปแล้ว AI สำคัญมาก",
        call_to_action="กด like และ subscribe",
        title_suggestions=["AI 2025: สิ่งที่คุณต้องรู้"],
        hashtags=["#AI", "#technology"],
        thumbnail_concept="แสดง AI robot"
    )
    
    # สร้าง thumbnail
    thumbnail_gen = ThumbnailGenerator()
    thumbnails = await thumbnail_gen.generate_thumbnail(
        title="AI 2025: สิ่งที่คุณต้องรู้",
        content_type="tech",
        platform="youtube"
    )
    
    # สร้าง visual plan
    visual_planner = VisualPlanner()
    visual_plan = await visual_planner.create_visual_plan(script, "educational")
    
    # หา images
    asset_manager = ImageAssetManager()
    images = await asset_manager.find_relevant_images(["AI", "technology", "robot"])
    
    print("Thumbnail designs generated:", len(thumbnails["designs"]))
    print("Visual scenes planned:", len(visual_plan.scenes))
    print("Related images found:", len(images))
    
    return {
        "thumbnails": thumbnails,
        "visual_plan": visual_plan,
        "assets": images
    }

if __name__ == "__main__":
    asyncio.run(main())