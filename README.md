# 🚀 AI Content Factory

> **อัตโนมัติการสร้างเนื้อหา จับเทรนด์ได้ทันใจ สร้างรายได้แบบ 24/7**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](./VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](./docker-compose.yml)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

AI Content Factory เป็นระบบอัตโนมัติที่ครบวงจร สำหรับการสร้างเนื้อหาจากเทรนด์ที่กำลังฮิต ด้วยพลัง AI หลากหลายรูปแบบ ตั้งแต่การวิเคราะห์เทรนด์ สร้างเนื้อหา ไปจนถึงการอัปโหลดไปยังแพลตฟอร์มต่างๆ อัตโนมัติ

## 🎯 **ความสามารถหลัก**

### 📊 **Trend Intelligence**
- **จับเทรนด์แบบ Real-time** จาก YouTube, Google Trends, Twitter, Reddit
- **AI Analysis** ประเมินความน่าสนใจ และโอกาสสร้างรายได้
- **Opportunity Scoring** จัดอันดับเทรนด์ที่คุ้มค่าที่สุด

### 🤖 **AI Content Generation** 
- **Multi-tier AI Services** รองรับ Budget → Premium (Groq → OpenAI → Claude)
- **Content Pipeline** สร้าง Script, Visual Plan, Audio Plan ครบวงจร
- **Platform Optimization** ปรับเนื้อหาให้เหมาะกับแต่ละแพลตฟอร์ม

### 🎬 **Automated Production**
- **Text-to-Speech** หลากหลาย voices และคุณภาพ
- **Image Generation** Stable Diffusion, Leonardo.AI, Midjourney
- **Video Assembly** รวมภาพ เสียง และ text overlay อัตโนมัติ

### 📱 **Multi-Platform Upload**
- **YouTube** - อัปโหลดพร้อม SEO optimization
- **TikTok** - รูปแบบสั้น เร็ว ทันเทรนด์
- **Instagram** - Reels และ Stories
- **Facebook** - Video posts และ Stories

## 🏗️ **สถาปัตยกรรมระบบ**

```
📊 Trend Monitor → 🤖 AI Director → 🎬 Content Engine → 📱 Platform Manager
       ↓                ↓              ↓              ↓
   MongoDB/SQL     LangChain      FFmpeg/PIL     Platform APIs
```

### **Core Services**
- **Trend Monitor** - เก็บและวิเคราะห์เทรนด์
- **Content Engine** - สร้างเนื้อหาด้วย AI
- **Platform Manager** - จัดการการอัปโหลด
- **Web Dashboard** - UI สำหรับควบคุมระบบ

## 🚀 **Quick Start**

### **1. ติดตั้งระบบ**

```bash
# Clone repository
git clone https://github.com/your-username/ai-content-factory.git
cd ai-content-factory

# Setup environment
make setup

# Start development environment
make dev
```

### **2. เข้าถึงระบบ**

- **📱 Main Dashboard:** http://localhost:5000
- **📊 Monitoring:** http://localhost:3001  
- **🔄 n8n Workflows:** http://localhost:5678
- **📈 Grafana:** http://localhost:3000

### **3. การตั้งค่าเบื้องต้น**

```bash
# Copy environment file
cp .env.example .env

# Edit your API keys
nano .env
```

## ⚙️ **Environment Variables**

```bash
# AI Services
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_claude_key

# Platform APIs
YOUTUBE_API_KEY=your_youtube_key
TIKTOK_ACCESS_TOKEN=your_tiktok_token

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/content_factory
REDIS_URL=redis://localhost:6379

# Quality Settings
QUALITY_TIER=budget  # budget|balanced|premium
```

## 📦 **Installation Methods**

### **Method 1: Docker (แนะนำ)**

```bash
# เริ่มระบบทั้งหมด
make dev

# หรือใช้ docker-compose โดยตรง
docker-compose up -d
```

### **Method 2: การติดตั้งแบบ Manual**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Setup database
make db-setup

# Install Node.js dependencies (สำหรับ dashboard)
cd web-dashboard
npm install
npm start
```

### **Method 3: Kubernetes**

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/
```

## 💡 **การใช้งานเบื้องต้น**

### **1. เก็บเทรนด์**

```bash
# Manual trend collection
curl -X POST http://localhost:5000/api/trends/collect

# หรือผ่าน Python
python -c "from trend_monitor.app import collect_trends; collect_trends()"
```

### **2. ดูโอกาสเนื้อหา**

```bash
# Get content opportunities
curl http://localhost:5000/api/opportunities/top

# ผลลัพธ์ตัวอย่าง:
{
  "opportunities": [
    {
      "trend": "AI Tools 2025",
      "score": 9.2,
      "competition": "medium",
      "suggested_angles": [
        "Top 10 AI Tools มือใหม่ต้องรู้",
        "AI Tools ฟรี vs เสียเงิน คุ้มไหม?",
        "รีวิว AI Tools ใหม่ล่าสุด"
      ]
    }
  ]
}
```

### **3. สร้างเนื้อหา**

```bash
# Create content from opportunity
curl -X POST http://localhost:5000/api/content/generate \
  -H "Content-Type: application/json" \
  -d '{"opportunity_id": "123", "platform": ["youtube", "tiktok"]}'
```

## 🎛️ **Dashboard Features**

### **📊 Trends Dashboard**
- เทรนด์ล่าสุด Real-time
- กราฟความนิยม
- การจัดอันดับตามโซน

### **💡 Opportunities View**  
- โอกาสเนื้อหาที่คัดสรรแล้ว
- คะแนน ROI และ Competition
- Suggested Content Angles

### **🎬 Content Pipeline**
- ติดตามสถานะการสร้างเนื้อหา
- ดูตัวอย่างเนื้อหาก่อนเผยแพร่
- แก้ไขและปรับปรุงเนื้อหา

### **📈 Performance Analytics**
- สถิติการเข้าถึง
- รายได้ต่อเนื้อหา  
- เปรียบเทียบประสิทธิภาพ

## 🔧 **Configuration**

### **Quality Tiers**

```yaml
# config/quality_tiers.yaml
budget:
  text_ai: "groq"
  image_ai: "stable_diffusion_local"
  tts: "gtts"
  cost_per_video: 15

balanced:
  text_ai: "openai"
  image_ai: "leonardo_ai"  
  tts: "azure_tts"
  cost_per_video: 45

premium:
  text_ai: "claude"
  image_ai: "midjourney"
  tts: "elevenlabs"
  cost_per_video: 150
```

### **Platform Settings**

```yaml
# config/platform_configs/youtube.yaml
youtube:
  max_title_length: 100
  max_description_length: 5000
  optimal_video_length: 480  # 8 minutes
  thumbnail_size: [1280, 720]
  category_id: 28  # Science & Technology
```

## 🧪 **Testing**

```bash
# Run all tests
make test

# Unit tests only  
make test-unit

# Integration tests
make test-integration

# Code linting
make lint
```

## 📊 **Monitoring & Analytics**

### **System Monitoring**
```bash
# Start monitoring stack
make monitor

# View logs
make logs

# Health check
make health
```

### **Performance Metrics**
- **Trend Collection Rate** - เทรนด์ต่อชั่วโมง
- **Content Generation Time** - เวลาเฉลี่ยในการสร้าง
- **Upload Success Rate** - อัตราความสำเร็จการอัปโหลด
- **Cost Per Content** - ต้นทุนต่อเนื้อหา

## 🔄 **n8n Workflows**

### **Master Workflow**
1. **Trend Collection** (ทุก 6 ชั่วโมง)
2. **AI Analysis** → Content Opportunities
3. **User Notification** → Dashboard Alert
4. **Content Generation** → Platform Upload
5. **Performance Tracking** → Analytics Update

### **Workflow Management**
```bash
# Import n8n workflows
cd n8n-workflows
./import-workflows.sh

# หรือ import ผ่าน n8n UI
# http://localhost:5678 → Import → เลือกไฟล์ .json
```

## 🎯 **Development Roadmap**

### **Phase 1: Foundation (✅ Complete)**
- [x] Basic trend collection system
- [x] Database schema and models
- [x] Core AI integration
- [x] Simple web dashboard
- [x] Docker containerization

### **Phase 2: Content Engine (🚧 In Progress)**
- [x] Multi-tier AI services
- [x] Content pipeline architecture
- [ ] Video generation pipeline
- [ ] Advanced content optimization
- [ ] Template system

### **Phase 3: Platform Integration (📋 Planned)**
- [ ] Real YouTube API integration
- [ ] TikTok upload automation
- [ ] Instagram/Facebook posting
- [ ] Cross-platform scheduling

### **Phase 4: Advanced Features (🔮 Future)**
- [ ] Machine learning optimization
- [ ] Competitor analysis
- [ ] A/B testing framework
- [ ] Multi-language support

## 🏢 **Architecture Deep Dive**

### **Microservices Design**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trend Monitor │◄──►│  Content Engine │◄──►│Platform Manager│
│                 │    │                 │    │                 │
│ - YouTube API   │    │ - AI Director   │    │ - Upload Queue  │
│ - Google Trends │    │ - Content Gen   │    │ - Platform APIs │
│ - Social Media  │    │ - Quality Tiers │    │ - Scheduling    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Web Dashboard │
                    │                 │
                    │ - React Frontend│
                    │ - Real-time UI  │
                    │ - Analytics     │
                    └─────────────────┘
```

### **Data Flow**

```
Raw Trends → AI Analysis → Content Ideas → User Selection → Content Generation → Platform Upload → Performance Tracking
```

## 💰 **Cost Optimization**

### **Budget Tier (฿15-30/วิดีโอ)**
- **Text AI:** Groq (ฟรี/ถูก)
- **Image:** Stable Diffusion Local
- **Voice:** Google Text-to-Speech
- **เหมาะสำหรับ:** เริ่มต้น, ทดสอบระบบ

### **Balanced Tier (฿45-80/วิดีโอ)**  
- **Text AI:** OpenAI GPT-4
- **Image:** Leonardo.AI
- **Voice:** Azure TTS
- **เหมาะสำหรับ:** การใช้งานจริง, คุณภาพดี

### **Premium Tier (฿150-300/วิดีโอ)**
- **Text AI:** Claude 3.5 Sonnet
- **Image:** Midjourney API
- **Voice:** ElevenLabs
- **เหมาะสำหรับ:** เนื้อหาพรีเมียม, แบรนด์

## 🔐 **Security & Best Practices**

### **API Key Management**
```bash
# ไม่ควรเก็บ API keys ในโค้ด
export OPENAI_API_KEY="your-key"

# ใช้ .env files
echo "OPENAI_API_KEY=your-key" >> .env

# Kubernetes secrets  
kubectl create secret generic api-keys --from-env-file=.env
```

### **Rate Limiting**
```python
# Built-in rate limiting
from shared.utils.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, time_window=3600)
# Max 100 requests per hour per service
```

### **Error Handling**
- **Graceful Degradation** - ถ้า premium AI fail ใช้ budget tier
- **Retry Logic** - ลองใหม่อัตโนมัติสำหรับ temporary failures  
- **Circuit Breaker** - หยุดเรียก service ที่ fail บ่อย

## 🚀 **Deployment Options**

### **Local Development**
```bash
# รันบนเครื่องตัวเอง
make dev
```

### **VPS/Cloud (แนะนำ)**
```bash
# Deploy to staging
make deploy-staging

# Deploy to production  
make deploy-prod
```

### **Kubernetes (Scale)**
```bash
# Apply manifests
kubectl apply -f kubernetes/

# Auto-scaling
kubectl apply -f kubernetes/hpa/
```

## 📈 **Performance Benchmarks**

### **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4GB | 8GB+ |
| **CPU** | 2 cores | 4+ cores |
| **Storage** | 20GB | 100GB+ SSD |
| **Bandwidth** | 10Mbps | 50Mbps+ |

### **Expected Performance**

| Metric | Budget Tier | Premium Tier |
|--------|-------------|--------------|
| **Trends/hour** | 1,000+ | 5,000+ |
| **Content generation** | 2-5 min | 5-10 min |
| **Cost per video** | ฿15-30 | ฿150-300 |
| **Quality score** | 7/10 | 9/10 |

## 🤝 **Contributing**

### **Development Setup**
```bash
# Fork the repository
git clone https://github.com/your-username/ai-content-factory.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and commit
git commit -m "Add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

### **Code Standards**
- **Python:** Follow PEP 8, use Black for formatting
- **JavaScript:** ESLint + Prettier
- **Commits:** Conventional commit messages
- **Tests:** Maintain >80% coverage

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Database Connection Failed**
```bash
# Check if PostgreSQL is running
make status

# Reset database
make db-reset
```

#### **AI API Errors**  
```bash
# Check API key validity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Switch to budget tier
export QUALITY_TIER=budget
```

#### **Platform Upload Failed**
```bash
# Check platform credentials
python -c "from platform_manager.app import test_credentials; test_credentials()"

# View upload logs  
make logs-service platform-manager
```

### **Performance Issues**
```bash
# Monitor system resources
make monitor

# Check service health
make health

# View performance metrics
curl http://localhost:5000/api/metrics
```

## 📚 **Documentation**

- **📖 [User Guide](./docs/guides/user-guide.md)** - คู่มือผู้ใช้งาน
- **⚙️ [Admin Guide](./docs/guides/admin-guide.md)** - คู่มือผู้ดูแลระบบ  
- **🔧 [API Documentation](./docs/api/)** - REST API references
- **🐳 [Docker Guide](./docs/deployment/docker-setup.md)** - Docker deployment
- **☸️ [Kubernetes Guide](./docs/deployment/kubernetes-setup.md)** - K8s deployment

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 **Acknowledgments**

- **OpenAI** - GPT models for content generation
- **Anthropic** - Claude AI for advanced analysis
- **Groq** - Fast inference for budget tier
- **YouTube, TikTok APIs** - Platform integrations
- **n8n** - Workflow automation framework

## 📞 **Support**

- **🐛 Bug Reports:** [GitHub Issues](https://github.com/your-username/ai-content-factory/issues)
- **💡 Feature Requests:** [GitHub Discussions](https://github.com/your-username/ai-content-factory/discussions)
- **💬 Community:** [Discord Server](https://discord.gg/your-invite)
- **📧 Email:** support@aicontentfactory.com

---

## 🎉 **Get Started Today!**

```bash
git clone https://github.com/your-username/ai-content-factory.git
cd ai-content-factory
make quick-start
```

**ไปสร้างเนื้อหาไวรัลกันเลย! 🚀🎬✨**