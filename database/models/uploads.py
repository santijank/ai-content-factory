# database/models/uploads.py
"""
Upload Model - จัดการข้อมูลการอัปโหลดเนื้อหาไป platforms
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .base import BaseModel


class Upload(BaseModel):
    """Model สำหรับเก็บข้อมูลการอัปโหลด"""
    
    __tablename__ = 'uploads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('content_items.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # youtube, tiktok, instagram, etc.
    platform_id = Column(String(255), nullable=True)  # ID จาก platform
    url = Column(Text, nullable=True)  # URL ของเนื้อหาที่อัปโหลด
    
    # Upload Status
    status = Column(String(20), nullable=False, default='pending')  # pending, uploading, completed, failed
    upload_progress = Column(Integer, default=0)  # 0-100%
    
    # Platform-specific metadata
    metadata = Column(JSON, default=dict)  # title, description, tags, etc.
    platform_response = Column(JSON, default=dict)  # Response จาก platform API
    
    # Performance data
    performance_data = Column(JSON, default=dict)  # views, likes, comments, shares
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # เวลาที่จะอัปโหลด
    uploaded_at = Column(DateTime(timezone=True), nullable=True)  # เวลาที่อัปโหลดสำเร็จ
    last_performance_update = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relations
    content_item = relationship("ContentItem", back_populates="uploads")
    performance_metrics = relationship("PerformanceMetric", back_populates="upload", cascade="all, delete-orphan")
    
    def to_dict(self):
        """แปลงเป็น dictionary"""
        return {
            'id': str(self.id),
            'content_id': str(self.content_id),
            'platform': self.platform,
            'platform_id': self.platform_id,
            'url': self.url,
            'status': self.status,
            'upload_progress': self.upload_progress,
            'metadata': self.metadata,
            'performance_data': self.performance_data,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'last_performance_update': self.last_performance_update.isoformat() if self.last_performance_update else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_status(self, status: str, error_message: str = None):
        """อัปเดตสถานะการอัปโหลด"""
        self.status = status
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)
        
        if status == 'completed':
            self.uploaded_at = datetime.now(timezone.utc)
            self.upload_progress = 100
        elif status == 'failed':
            self.retry_count += 1
    
    def update_performance_data(self, performance_data: dict):
        """อัปเดตข้อมูลประสิทธิภาพ"""
        if self.performance_data is None:
            self.performance_data = {}
        
        self.performance_data.update(performance_data)
        self.last_performance_update = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def can_retry(self) -> bool:
        """ตรวจสอบว่าสามารถลองอัปโหลดใหม่ได้หรือไม่"""
        return self.retry_count < self.max_retries and self.status == 'failed'
    
    @property
    def is_successful(self) -> bool:
        """ตรวจสอบว่าอัปโหลดสำเร็จหรือไม่"""
        return self.status == 'completed'
    
    @property
    def is_pending(self) -> bool:
        """ตรวจสอบว่ากำลังรออัปโหลดหรือไม่"""
        return self.status in ['pending', 'uploading']
    
    def get_view_count(self) -> int:
        """ดึงจำนวน views"""
        return self.performance_data.get('views', 0)
    
    def get_engagement_rate(self) -> float:
        """คำนวณ engagement rate"""
        views = self.get_view_count()
        if views == 0:
            return 0.0
        
        likes = self.performance_data.get('likes', 0)
        comments = self.performance_data.get('comments', 0)
        shares = self.performance_data.get('shares', 0)
        
        engagement = likes + comments + shares
        return (engagement / views) * 100


class UploadTemplate(BaseModel):
    """Template สำหรับการอัปโหลดแต่ละ platform"""
    
    __tablename__ = 'upload_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)
    
    # Template data
    title_template = Column(Text, nullable=True)  # Template สำหรับ title
    description_template = Column(Text, nullable=True)  # Template สำหรับ description
    tags_template = Column(JSON, default=list)  # Template สำหรับ tags
    
    # Default settings
    default_metadata = Column(JSON, default=dict)  # การตั้งค่าเริ่มต้น
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'platform': self.platform,
            'title_template': self.title_template,
            'description_template': self.description_template,
            'tags_template': self.tags_template,
            'default_metadata': self.default_metadata,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def apply_template(self, content_data: dict) -> dict:
        """ใช้ template กับข้อมูลเนื้อหา"""
        result = self.default_metadata.copy()
        
        # Apply title template
        if self.title_template:
            result['title'] = self._apply_template_string(self.title_template, content_data)
        
        # Apply description template
        if self.description_template:
            result['description'] = self._apply_template_string(self.description_template, content_data)
        
        # Apply tags template
        if self.tags_template:
            result['tags'] = []
            for tag_template in self.tags_template:
                tag = self._apply_template_string(tag_template, content_data)
                if tag:
                    result['tags'].append(tag)
        
        # Update usage
        self.usage_count += 1
        self.last_used = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        return result
    
    def _apply_template_string(self, template: str, data: dict) -> str:
        """ใช้ template string กับข้อมูล"""
        try:
            # Simple template substitution
            for key, value in data.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        except Exception:
            return template


# database/models/performance_metrics.py
"""
Performance Metrics Model - จัดการข้อมูลประสิทธิภาพของเนื้อหา
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Boolean, ForeignKey, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .base import BaseModel


class PerformanceMetric(BaseModel):
    """Model สำหรับเก็บ metrics การทำงานของเนื้อหา"""
    
    __tablename__ = 'performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey('uploads.id'), nullable=False)
    
    # Core metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Advanced metrics
    watch_time_minutes = Column(Float, default=0.0)  # สำหรับวิดีโอ
    click_through_rate = Column(Float, default=0.0)  # CTR %
    engagement_rate = Column(Float, default=0.0)  # Engagement %
    
    # Revenue metrics
    revenue = Column(Numeric(10, 2), default=0.00)
    ad_revenue = Column(Numeric(10, 2), default=0.00)
    sponsor_revenue = Column(Numeric(10, 2), default=0.00)
    
    # Audience metrics
    unique_viewers = Column(Integer, default=0)
    subscriber_gain = Column(Integer, default=0)
    subscriber_loss = Column(Integer, default=0)
    
    # Geographic and demographic data
    audience_data = Column(JSON, default=dict)  # อายุ, เพศ, ประเทศ
    traffic_sources = Column(JSON, default=dict)  # มาจากไหน (search, suggested, etc.)
    
    # Timing data
    measured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    data_collection_method = Column(String(50), default='api')  # api, manual, estimated
    
    # Relations
    upload = relationship("Upload", back_populates="performance_metrics")
    
    def to_dict(self):
        """แปลงเป็น dictionary"""
        return {
            'id': str(self.id),
            'upload_id': str(self.upload_id),
            'views': self.views,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'comments': self.comments,
            'shares': self.shares,
            'watch_time_minutes': float(self.watch_time_minutes or 0),
            'click_through_rate': float(self.click_through_rate or 0),
            'engagement_rate': float(self.engagement_rate or 0),
            'revenue': float(self.revenue or 0),
            'ad_revenue': float(self.ad_revenue or 0),
            'sponsor_revenue': float(self.sponsor_revenue or 0),
            'unique_viewers': self.unique_viewers,
            'subscriber_gain': self.subscriber_gain,
            'subscriber_loss': self.subscriber_loss,
            'audience_data': self.audience_data,
            'traffic_sources': self.traffic_sources,
            'measured_at': self.measured_at.isoformat(),
            'data_collection_method': self.data_collection_method,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_engagement_rate(self):
        """คำนวณ engagement rate"""
        if self.views == 0:
            self.engagement_rate = 0.0
        else:
            total_engagement = self.likes + self.comments + self.shares
            self.engagement_rate = (total_engagement / self.views) * 100
        
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_ctr(self, impressions: int):
        """คำนวณ click-through rate"""
        if impressions == 0:
            self.click_through_rate = 0.0
        else:
            self.click_through_rate = (self.views / impressions) * 100
        
        self.updated_at = datetime.now(timezone.utc)
    
    def update_metrics(self, new_metrics: dict):
        """อัปเดต metrics"""
        for key, value in new_metrics.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        # คำนวณ engagement rate ใหม่
        self.calculate_engagement_rate()
        
        self.measured_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    @property
    def total_engagement(self) -> int:
        """รวม engagement ทั้งหมด"""
        return self.likes + self.comments + self.shares
    
    @property
    def net_subscriber_change(self) -> int:
        """การเปลี่ยนแปลงจำนวนผู้ติดตาม"""
        return self.subscriber_gain - self.subscriber_loss
    
    @property
    def total_revenue(self) -> float:
        """รายได้รวม"""
        return float(self.revenue + self.ad_revenue + self.sponsor_revenue)
    
    def get_rpm(self) -> float:
        """Revenue Per Mille (RPM) - รายได้ต่อ 1000 views"""
        if self.views == 0:
            return 0.0
        return (self.total_revenue / self.views) * 1000


class ContentAnalytics(BaseModel):
    """Analytics สำหรับเนื้อหา (รวมข้อมูลจากหลาย uploads)"""
    
    __tablename__ = 'content_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('content_items.id'), nullable=False)
    
    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, total
    
    # Aggregated metrics
    total_views = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)
    average_engagement_rate = Column(Float, default=0.0)
    
    total_revenue = Column(Numeric(10, 2), default=0.00)
    total_cost = Column(Numeric(10, 2), default=0.00)  # ค่าใช้จ่ายในการสร้าง
    roi_percentage = Column(Float, default=0.0)  # Return on Investment
    
    # Platform breakdown
    platform_performance = Column(JSON, default=dict)  # performance แยกตาม platform
    
    # Best performing metrics
    best_platform = Column(String(50), nullable=True)
    best_content_type = Column(String(50), nullable=True)
    peak_performance_date = Column(DateTime(timezone=True), nullable=True)
    
    # Trends and insights
    performance_trend = Column(String(20), default='stable')  # increasing, decreasing, stable
    insights = Column(JSON, default=list)  # AI-generated insights
    
    # Relations
    content_item = relationship("ContentItem", back_populates="analytics")
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'content_id': str(self.content_id),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'period_type': self.period_type,
            'total_views': self.total_views,
            'total_engagement': self.total_engagement,
            'average_engagement_rate': float(self.average_engagement_rate or 0),
            'total_revenue': float(self.total_revenue or 0),
            'total_cost': float(self.total_cost or 0),
            'roi_percentage': float(self.roi_percentage or 0),
            'platform_performance': self.platform_performance,
            'best_platform': self.best_platform,
            'best_content_type': self.best_content_type,
            'peak_performance_date': self.peak_performance_date.isoformat() if self.peak_performance_date else None,
            'performance_trend': self.performance_trend,
            'insights': self.insights,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_roi(self):
        """คำนวณ ROI"""
        if self.total_cost == 0:
            self.roi_percentage = 0.0
        else:
            profit = self.total_revenue - self.total_cost
            self.roi_percentage = (profit / self.total_cost) * 100
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_insight(self, insight: str, confidence: float = 1.0):
        """เพิ่ม insight"""
        if self.insights is None:
            self.insights = []
        
        self.insights.append({
            'text': insight,
            'confidence': confidence,
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
        
        self.updated_at = datetime.now(timezone.utc)


class SystemMetrics(BaseModel):
    """Metrics ของระบบโดยรวม"""
    
    __tablename__ = 'system_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    period_type = Column(String(20), default='daily')  # hourly, daily, weekly, monthly
    
    # System usage
    trends_collected = Column(Integer, default=0)
    opportunities_generated = Column(Integer, default=0)
    content_created = Column(Integer, default=0)
    uploads_completed = Column(Integer, default=0)
    
    # Performance
    average_response_time_ms = Column(Float, default=0.0)
    success_rate_percentage = Column(Float, default=100.0)
    error_count = Column(Integer, default=0)
    
    # Costs and revenue
    total_ai_cost = Column(Numeric(10, 2), default=0.00)
    total_platform_cost = Column(Numeric(10, 2), default=0.00)
    estimated_revenue = Column(Numeric(10, 2), default=0.00)
    
    # Resource usage
    cpu_usage_avg = Column(Float, default=0.0)
    memory_usage_avg = Column(Float, default=0.0)
    storage_used_gb = Column(Float, default=0.0)
    
    # Platform-specific data
    platform_stats = Column(JSON, default=dict)  # stats แยกตาม platform
    
    # AI service usage
    ai_service_stats = Column(JSON, default=dict)  # usage stats ของ AI services
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'date': self.date.isoformat(),
            'period_type': self.period_type,
            'trends_collected': self.trends_collected,
            'opportunities_generated': self.opportunities_generated,
            'content_created': self.content_created,
            'uploads_completed': self.uploads_completed,
            'average_response_time_ms': float(self.average_response_time_ms or 0),
            'success_rate_percentage': float(self.success_rate_percentage or 0),
            'error_count': self.error_count,
            'total_ai_cost': float(self.total_ai_cost or 0),
            'total_platform_cost': float(self.total_platform_cost or 0),
            'estimated_revenue': float(self.estimated_revenue or 0),
            'cpu_usage_avg': float(self.cpu_usage_avg or 0),
            'memory_usage_avg': float(self.memory_usage_avg or 0),
            'storage_used_gb': float(self.storage_used_gb or 0),
            'platform_stats': self.platform_stats,
            'ai_service_stats': self.ai_service_stats,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_stats(self, new_stats: dict):
        """อัปเดตสถิติ"""
        for key, value in new_stats.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        self.updated_at = datetime.now(timezone.utc)
    
    @property
    def total_cost(self) -> float:
        """ค่าใช้จ่ายรวม"""
        return float(self.total_ai_cost + self.total_platform_cost)
    
    @property
    def profit(self) -> float:
        """กำไร"""
        return float(self.estimated_revenue) - self.total_cost
    
    @property
    def roi_percentage(self) -> float:
        """ROI เป็น %"""
        if self.total_cost == 0:
            return 0.0
        return (self.profit / self.total_cost) * 100


# Migration script updates needed in existing models
"""
เพิ่ม relationships ใน existing models:

# ใน database/models/content_items.py
class ContentItem(BaseModel):
    # ... existing fields ...
    uploads = relationship("Upload", back_populates="content_item", cascade="all, delete-orphan")
    analytics = relationship("ContentAnalytics", back_populates="content_item", cascade="all, delete-orphan")

# ใน database/models/trends.py  
class Trend(BaseModel):
    # ... existing fields ...
    # อาจเพิ่ม performance tracking ถ้าต้องการ

# ใน database/models/content_opportunities.py
class ContentOpportunity(BaseModel):
    # ... existing fields ...
    # อาจเพิ่ม success tracking ถ้าต้องการ
"""