"""
Content Plan Data Models
โมเดลข้อมูลสำหรับการจัดการแผนเนื้อหา, โอกาส, และ assets
รองรับการ serialize/deserialize และ validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

class ContentStatus(Enum):
    """สถานะเนื้อหา"""
    PLANNED = "planned"
    IN_PRODUCTION = "in_production"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class EngagementLevel(Enum):
    """ระดับ engagement ที่คาดหวัง"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VIRAL = "viral"

class ProductionDifficulty(Enum):
    """ระดับความยากในการผลิต"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class PlatformType(Enum):
    """ประเภทแพลตฟอร์ม"""
    YOUTUBE = "YouTube"
    TIKTOK = "TikTok"
    INSTAGRAM = "Instagram"
    FACEBOOK = "Facebook"
    TWITTER = "Twitter"
    LINKEDIN = "LinkedIn"

@dataclass
class ContentMetrics:
    """ตัวชี้วัดเนื้อหา"""
    expected_views: int = 0
    expected_engagement_rate: float = 0.0
    expected_shares: int = 0
    expected_comments: int = 0
    expected_likes: int = 0
    confidence_score: float = 0.0  # ความมั่นใจในการคาดการณ์ (0-1)
    
    # Actual metrics (filled after publication)
    actual_views: Optional[int] = None
    actual_engagement_rate: Optional[float] = None
    actual_shares: Optional[int] = None
    actual_comments: Optional[int] = None
    actual_likes: Optional[int] = None
    measured_at: Optional[datetime] = None
    
    def calculate_performance_ratio(self) -> Dict[str, float]:
        """คำนวณอัตราส่วนประสิทธิภาพ actual vs expected"""
        if not self.actual_views:
            return {"status": "no_data"}
        
        return {
            "views_ratio": self.actual_views / max(self.expected_views, 1),
            "engagement_ratio": (self.actual_engagement_rate or 0) / max(self.expected_engagement_rate, 0.01),
            "shares_ratio": (self.actual_shares or 0) / max(self.expected_shares, 1),
            "overall_performance": (
                (self.actual_views / max(self.expected_views, 1) +
                 (self.actual_engagement_rate or 0) / max(self.expected_engagement_rate, 0.01)) / 2
            )
        }

@dataclass
class ContentAsset:
    """ทรัพยากรเนื้อหา (ไฟล์, รูปภาพ, เสียง)"""
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_type: str = ""  # video, image, audio, text, thumbnail
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None  # สำหรับ video/audio (วินาที)
    resolution: Optional[str] = None  # สำหรับ video/image (1920x1080)
    format: Optional[str] = None  # mp4, jpg, png, wav, etc.
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # user_id หรือ ai_service
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "duration": self.duration,
            "resolution": self.resolution,
            "format": self.format,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "metadata": self.metadata
        }

@dataclass
class ContentScript:
    """สคริปต์เนื้อหา"""
    script_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Main script sections
    hook: str = ""
    hook_duration: str = "0-5s"
    introduction: str = ""
    main_content: List[Dict[str, str]] = field(default_factory=list)  # [{text, duration, visual}]
    conclusion: str = ""
    call_to_action: str = ""
    
    # Script metadata
    total_duration: str = ""
    word_count: int = 0
    speaking_pace: str = "normal"  # slow, normal, fast
    tone: str = "friendly"
    target_platform: str = ""
    
    # Production notes
    visual_directions: List[str] = field(default_factory=list)
    audio_notes: List[str] = field(default_factory=list)
    editing_suggestions: List[str] = field(default_factory=list)
    
    # SEO and metadata
    title_suggestions: List[str] = field(default_factory=list)
    description_points: List[str] = field(default_factory=list)
    thumbnail_concepts: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def get_estimated_word_count(self) -> int:
        """คำนวณจำนวนคำโดยประมาณ"""
        total_text = f"{self.hook} {self.introduction} {self.conclusion} {self.call_to_action}"
        for section in self.main_content:
            total_text += f" {section.get('text', '')}"
        return len(total_text.split())
    
    def update_word_count(self):
        """อัปเดตจำนวนคำ"""
        self.word_count = self.get_estimated_word_count()
        self.last_modified = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "script_id": self.script_id,
            "hook": self.hook,
            "hook_duration": self.hook_duration,
            "introduction": self.introduction,
            "main_content": self.main_content,
            "conclusion": self.conclusion,
            "call_to_action": self.call_to_action,
            "total_duration": self.total_duration,
            "word_count": self.word_count,
            "speaking_pace": self.speaking_pace,
            "tone": self.tone,
            "target_platform": self.target_platform,
            "visual_directions": self.visual_directions,
            "audio_notes": self.audio_notes,
            "editing_suggestions": self.editing_suggestions,
            "title_suggestions": self.title_suggestions,
            "description_points": self.description_points,
            "thumbnail_concepts": self.thumbnail_concepts,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "version": self.version
        }

@dataclass
class HashtagStrategy:
    """กลยุทธ์ hashtag"""
    platform: str
    trending_hashtags: List[str] = field(default_factory=list)
    niche_hashtags: List[str] = field(default_factory=list)
    branded_hashtags: List[str] = field(default_factory=list)
    long_tail_hashtags: List[str] = field(default_factory=list)
    
    # Strategy metadata
    recommended_set: List[str] = field(default_factory=list)  # คำแนะนำ hashtags ที่ควรใช้
    avoid_hashtags: List[str] = field(default_factory=list)   # hashtags ที่ไม่ควรใช้
    strategy_notes: str = ""
    
    # Performance data
    estimated_reach: Optional[int] = None
    competition_level: str = "medium"  # low, medium, high
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_all_hashtags(self) -> List[str]:
        """รวม hashtags ทั้งหมด"""
        all_tags = []
        all_tags.extend(self.trending_hashtags)
        all_tags.extend(self.niche_hashtags)
        all_tags.extend(self.branded_hashtags)
        all_tags.extend(self.long_tail_hashtags)
        return list(set(all_tags))  # Remove duplicates
    
    def get_optimized_set(self, max_count: int = 30) -> List[str]:
        """ได้ชุด hashtags ที่เหมาะสมที่สุด"""
        if self.recommended_set:
            return self.recommended_set[:max_count]
        
        # Create balanced mix if no recommendations
        optimized = []
        optimized.extend(self.trending_hashtags[:8])
        optimized.extend(self.niche_hashtags[:10])
        optimized.extend(self.branded_hashtags[:5])
        optimized.extend(self.long_tail_hashtags[:7])
        
        return optimized[:max_count]
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "platform": self.platform,
            "trending_hashtags": self.trending_hashtags,
            "niche_hashtags": self.niche_hashtags,
            "branded_hashtags": self.branded_hashtags,
            "long_tail_hashtags": self.long_tail_hashtags,
            "recommended_set": self.recommended_set,
            "avoid_hashtags": self.avoid_hashtags,
            "strategy_notes": self.strategy_notes,
            "estimated_reach": self.estimated_reach,
            "competition_level": self.competition_level,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class ContentOpportunity:
    """โอกาสเนื้อหา"""
    opportunity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    title: str = ""
    description: Union[str, List[str]] = ""
    platform: str = ""
    content_type: str = "video"  # video, image, carousel, story
    
    # AI-generated content elements
    hook: str = ""
    call_to_action: str = ""
    key_points: List[str] = field(default_factory=list)
    
    # Estimates and scoring
    estimated_engagement: str = "medium"  # low, medium, high, viral
    production_difficulty: str = "medium"  # easy, medium, hard, expert
    estimated_cost: float = 0.0
    estimated_production_time: str = "2-4 hours"
    viral_potential_score: float = 0.0  # 0-10
    
    # Content strategy
    target_audience: str = ""
    content_angle: str = ""
    unique_value_proposition: str = ""
    
    # Platform optimization
    optimal_timing: Optional[str] = None
    hashtag_strategy: Optional[HashtagStrategy] = None
    thumbnail_concept: str = ""
    
    # Content assets and script
    script: Optional[ContentScript] = None
    assets: List[ContentAsset] = field(default_factory=list)
    
    # Metrics and tracking
    metrics: ContentMetrics = field(default_factory=ContentMetrics)
    status: ContentStatus = ContentStatus.PLANNED
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "ai_director"
    last_updated: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def update_status(self, new_status: ContentStatus, notes: str = ""):
        """อัปเดตสถานะ"""
        self.status = new_status
        self.last_updated = datetime.now()
        if notes:
            self.notes += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
    
    def add_asset(self, asset: ContentAsset):
        """เพิ่ม asset"""
        self.assets.append(asset)
        self.last_updated = datetime.now()
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """แยกค่าใช้จ่าย"""
        return {
            "ai_generation": self.estimated_cost * 0.1,
            "content_production": self.estimated_cost * 0.6,
            "editing_post_production": self.estimated_cost * 0.2,
            "platform_optimization": self.estimated_cost * 0.1,
            "total": self.estimated_cost
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "opportunity_id": self.opportunity_id,
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "content_type": self.content_type,
            "hook": self.hook,
            "call_to_action": self.call_to_action,
            "key_points": self.key_points,
            "estimated_engagement": self.estimated_engagement,
            "production_difficulty": self.production_difficulty,
            "estimated_cost": self.estimated_cost,
            "estimated_production_time": self.estimated_production_time,
            "viral_potential_score": self.viral_potential_score,
            "target_audience": self.target_audience,
            "content_angle": self.content_angle,
            "unique_value_proposition": self.unique_value_proposition,
            "optimal_timing": self.optimal_timing,
            "hashtag_strategy": self.hashtag_strategy.to_dict() if self.hashtag_strategy else None,
            "thumbnail_concept": self.thumbnail_concept,
            "script": self.script.to_dict() if self.script else None,
            "assets": [asset.to_dict() for asset in self.assets],
            "metrics": {
                "expected_views": self.metrics.expected_views,
                "expected_engagement_rate": self.metrics.expected_engagement_rate,
                "confidence_score": self.metrics.confidence_score
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "last_updated": self.last_updated.isoformat(),
            "tags": self.tags,
            "notes": self.notes
        }

@dataclass
class ContentPlan:
    """แผนเนื้อหาหลัก"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Plan overview
    plan_name: str = ""
    description: str = ""
    
    # Source data
    trend_source: Dict[str, Any] = field(default_factory=dict)
    strategy: Dict[str, Any] = field(default_factory=dict)
    
    # Content opportunities
    opportunities: List[ContentOpportunity] = field(default_factory=list)
    
    # Plan metrics
    total_estimated_cost: float = 0.0
    estimated_timeline: str = ""
    success_metrics: List[str] = field(default_factory=list)
    expected_roi: Optional[float] = None
    
    # Optimization and recommendations
    optimization_recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    
    # Execution tracking
    progress_percentage: float = 0.0
    completed_opportunities: int = 0
    published_opportunities: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, paused, completed, archived
    
    def add_opportunity(self, opportunity: ContentOpportunity):
        """เพิ่มโอกาสเนื้อหา"""
        self.opportunities.append(opportunity)
        self.total_estimated_cost += opportunity.estimated_cost
        self.last_updated = datetime.now()
        self._update_progress()
    
    def remove_opportunity(self, opportunity_id: str):
        """ลบโอกาสเนื้อหา"""
        for i, opp in enumerate(self.opportunities):
            if opp.opportunity_id == opportunity_id:
                self.total_estimated_cost -= opp.estimated_cost
                del self.opportunities[i]
                self.last_updated = datetime.now()
                self._update_progress()
                break
    
    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[ContentOpportunity]:
        """หาโอกาสเนื้อหาด้วย ID"""
        for opp in self.opportunities:
            if opp.opportunity_id == opportunity_id:
                return opp
        return None
    
    def get_opportunities_by_platform(self, platform: str) -> List[ContentOpportunity]:
        """หาโอกาสเนื้อหาตาม platform"""
        return [opp for opp in self.opportunities if opp.platform == platform]
    
    def get_opportunities_by_status(self, status: ContentStatus) -> List[ContentOpportunity]:
        """หาโอกาสเนื้อหาตามสถานะ"""
        return [opp for opp in self.opportunities if opp.status == status]
    
    def _update_progress(self):
        """อัปเดตความคืบหน้า"""
        if not self.opportunities:
            self.progress_percentage = 0.0
            return
        
        self.completed_opportunities = len([
            opp for opp in self.opportunities 
            if opp.status in [ContentStatus.APPROVED, ContentStatus.PUBLISHED]
        ])
        
        self.published_opportunities = len([
            opp for opp in self.opportunities 
            if opp.status == ContentStatus.PUBLISHED
        ])
        
        self.progress_percentage = (self.completed_opportunities / len(self.opportunities)) * 100
    
    def get_platform_distribution(self) -> Dict[str, int]:
        """การกระจายโอกาสตาม platform"""
        distribution = {}
        for opp in self.opportunities:
            platform = opp.platform
            distribution[platform] = distribution.get(platform, 0) + 1
        return distribution
    
    def get_cost_by_platform(self) -> Dict[str, float]:
        """ต้นทุนแยกตาม platform"""
        costs = {}
        for opp in self.opportunities:
            platform = opp.platform
            costs[platform] = costs.get(platform, 0.0) + opp.estimated_cost
        return costs
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """สรุปประสิทธิภาพ"""
        total_expected_views = sum(opp.metrics.expected_views for opp in self.opportunities)
        avg_engagement_rate = sum(opp.metrics.expected_engagement_rate for opp in self.opportunities) / max(len(self.opportunities), 1)
        
        return {
            "total_opportunities": len(self.opportunities),
            "completed_count": self.completed_opportunities,
            "published_count": self.published_opportunities,
            "progress_percentage": self.progress_percentage,
            "total_estimated_cost": self.total_estimated_cost,
            "total_expected_views": total_expected_views,
            "average_engagement_rate": avg_engagement_rate,
            "platform_distribution": self.get_platform_distribution(),
            "cost_by_platform": self.get_cost_by_platform()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "description": self.description,
            "trend_source": self.trend_source,
            "strategy": self.strategy,
            "opportunities": [opp.to_dict() for opp in self.opportunities],
            "total_estimated_cost": self.total_estimated_cost,
            "estimated_timeline": self.estimated_timeline,
            "success_metrics": self.success_metrics,
            "expected_roi": self.expected_roi,
            "optimization_recommendations": self.optimization_recommendations,
            "risk_factors": self.risk_factors,
            "best_practices": self.best_practices,
            "progress_percentage": self.progress_percentage,
            "completed_opportunities": self.completed_opportunities,
            "published_opportunities": self.published_opportunities,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "last_updated": self.last_updated.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentPlan':
        """สร้าง ContentPlan จาก dictionary"""
        
        # Parse opportunities
        opportunities = []
        for opp_data in data.get("opportunities", []):
            # Create ContentOpportunity from dict
            opp = ContentOpportunity(
                opportunity_id=opp_data.get("opportunity_id", str(uuid.uuid4())),
                title=opp_data.get("title", ""),
                description=opp_data.get("description", ""),
                platform=opp_data.get("platform", ""),
                content_type=opp_data.get("content_type", "video"),
                estimated_cost=opp_data.get("estimated_cost", 0.0),
                # Add other fields as needed
                status=ContentStatus(opp_data.get("status", "planned"))
            )
            opportunities.append(opp)
        
        # Create ContentPlan
        plan = cls(
            plan_id=data.get("plan_id", str(uuid.uuid4())),
            plan_name=data.get("plan_name", ""),
            description=data.get("description", ""),
            trend_source=data.get("trend_source", {}),
            strategy=data.get("strategy", {}),
            opportunities=opportunities,
            total_estimated_cost=data.get("total_estimated_cost", 0.0),
            estimated_timeline=data.get("estimated_timeline", ""),
            success_metrics=data.get("success_metrics", []),
            created_by=data.get("created_by", ""),
            status=data.get("status", "active")
        )
        
        # Parse timestamps
        if "created_at" in data:
            plan.created_at = datetime.fromisoformat(data["created_at"])
        if "last_updated" in data:
            plan.last_updated = datetime.fromisoformat(data["last_updated"])
        
        plan._update_progress()
        return plan

# Utility functions
def create_sample_content_plan() -> ContentPlan:
    """สร้าง ContentPlan ตัวอย่างสำหรับทดสอบ"""
    
    # Create sample opportunities
    opportunities = [
        ContentOpportunity(
            title="AI Video Generation Tutorial",
            description="How to create amazing videos with AI tools",
            platform="YouTube",
            estimated_cost=150.0,
            estimated_engagement="high",
            viral_potential_score=7.5
        ),
        ContentOpportunity(
            title="Quick AI Video Tips",
            description="30-second tips for AI video creation",
            platform="TikTok",
            estimated_cost=75.0,
            estimated_engagement="viral",
            viral_potential_score=9.0
        )
    ]
    
    # Create plan
    plan = ContentPlan(
        plan_name="AI Video Creation Content Series",
        description="Complete content series about AI video generation",
        opportunities=opportunities,
        success_metrics=["views", "engagement", "subscribers"],
        created_by="ai_director_test"
    )
    
    return plan

# Testing and validation
def test_content_models():
    """ทดสอบ Content Models"""
    
    print("Testing Content Models...")
    
    # Test ContentPlan
    plan = create_sample_content_plan()
    print(f"Created plan with {len(plan.opportunities)} opportunities")
    print(f"Total cost: ฿{plan.total_estimated_cost}")
    print(f"Platform distribution: {plan.get_platform_distribution()}")
    
    # Test serialization
    plan_dict = plan.to_dict()
    print(f"Serialized plan: {len(json.dumps(plan_dict))} characters")
    
    # Test deserialization
    restored_plan = ContentPlan.from_dict(plan_dict)
    print(f"Restored plan: {restored_plan.plan_name}")
    
    # Test opportunity management
    new_opportunity = ContentOpportunity(
        title="Instagram Reel",
        platform="Instagram",
        estimated_cost=100.0
    )
    
    plan.add_opportunity(new_opportunity)
    print(f"After adding opportunity: {len(plan.opportunities)} opportunities")
    print(f"Updated cost: ฿{plan.total_estimated_cost}")
    
    print("Content Models test completed ✓")

if __name__ == "__main__":
    test_content_models()