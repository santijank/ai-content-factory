# 🚀 Quick Start Guide

Get AI Content Factory up and running in under 10 minutes! This guide will take you from zero to creating your first AI-generated content.

---

## 📋 What You'll Learn

By the end of this guide, you'll be able to:
- ✅ Set up AI Content Factory locally
- ✅ Connect to trending data sources
- ✅ Generate your first AI content
- ✅ Publish to social media platforms
- ✅ Monitor performance analytics

**⏱️ Estimated Time: 10 minutes**

---

## 🎯 Prerequisites

Before we start, make sure you have:

### 💻 **System Requirements**
- **Node.js** 18+ ([Download here](https://nodejs.org/))
- **Docker** & Docker Compose ([Download here](https://www.docker.com/))
- **Git** ([Download here](https://git-scm.com/))
- **8GB RAM** minimum (16GB recommended)
- **10GB free disk space**

### 🔑 **API Keys** (Optional for trial)
- **OpenAI API Key** - For advanced content generation
- **YouTube API Key** - For YouTube publishing
- **Google Trends API** - For trend analysis

> 💡 **Don't have API keys?** No problem! You can start with our mock data and free tier services.

---

## ⚡ Quick Setup (5 minutes)

### Step 1: Clone the Repository

```bash
# Clone the project
git clone https://github.com/ai-content-factory/ai-content-factory.git
cd ai-content-factory

# Verify you're in the right directory
ls -la
# Should see: docker-compose.yml, package.json, README.md, etc.
```

### Step 2: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Open the .env file in your favorite editor
nano .env  # or code .env or vim .env
```

**🔧 Quick Configuration:**
```bash
# Basic setup (edit these in your .env file)
NODE_ENV=development
APP_URL=http://localhost:3000
API_BASE_URL=http://localhost:5000

# Database (Docker will handle these)
DATABASE_URL=postgresql://admin:dev_password@localhost:5432/ai_content_factory_dev
REDIS_URL=redis://localhost:6379/0

# AI Services (start with free tier)
DEFAULT_QUALITY_TIER=budget
GROQ_API_KEY=your_groq_key_here  # Free tier available
MOCK_AI_SERVICES=true            # Use this for testing without API keys
```

### Step 3: Start the System

```bash
# Start all services with one command
docker-compose up -d

# Wait for services to start (about 2-3 minutes)
echo "Waiting for services to start..."
sleep 30

# Check if everything is running
docker-compose ps
```

**Expected Output:**
```
✅ ai-content-postgres    Up (healthy)
✅ ai-content-redis       Up (healthy)  
✅ ai-content-engine      Up (healthy)
✅ ai-content-dashboard   Up (healthy)
✅ ai-content-n8n         Up (healthy)
```

### Step 4: Initialize the Database

```bash
# Run database migrations
docker-compose exec content-engine npm run db:migrate

# Seed with sample data
docker-compose exec content-engine npm run db:seed
```

### Step 5: Verify Setup

Open your browser and navigate to:

- **🖥️ Main Dashboard**: http://localhost:3000
- **⚙️ N8N Workflows**: http://localhost:5678 (admin/admin)
- **📊 API Health**: http://localhost:5000/health

**✅ Success!** You should see the AI Content Factory dashboard.

---

## 🎬 Your First AI Content (3 minutes)

Now let's create your first piece of content!

### Step 1: Access the Dashboard

1. **Go to** http://localhost:3000
2. **Click** "Get Started" or "Dashboard"

### Step 2: Explore Trending Topics

```bash
# Manually trigger trend collection (if needed)
curl -X POST http://localhost:5000/api/trends/collect

# Or use the dashboard
```

1. **Navigate to** "Trends" tab
2. **See trending topics** from various sources
3. **Click on any trend** with a high opportunity score (7+)

### Step 3: Generate Content

1. **Select a trending topic** you like
2. **Choose content type**: 
   - 📺 YouTube Video
   - 🎵 TikTok Short
   - 📷 Instagram Post
3. **Select quality tier**: Budget (free) or Premium
4. **Click "Generate Content"**

**⏳ Wait 2-5 minutes** while AI creates:
- 📝 Engaging script with hook and CTA
- 🎨 Eye-catching thumbnail/images
- 🔊 Professional narration audio
- 🎬 Assembled final video

### Step 4: Preview Your Content

1. **Review generated content** in the preview panel
2. **Check the script**, images, and video
3. **Make edits** if needed (coming in v1.1)
4. **Approve for publishing** or save as draft

---

## 📤 Publishing Your Content (2 minutes)

### Option 1: Manual Download

1. **Click "Download"** on your generated content
2. **Save files** to your computer
3. **Upload manually** to your preferred platforms

### Option 2: Automatic Publishing (Requires API Setup)

1. **Go to Settings** → **Platform Integration**
2. **Connect your accounts**:
   - YouTube (OAuth)
   - TikTok (API Key)
   - Instagram (Basic Display API)
3. **Enable auto-publishing**
4. **Click "Publish Now"** on your content

**🎉 Congratulations!** Your AI-generated content is now live!

---

## 📊 Monitor Performance

### Real-Time Analytics

1. **Navigate to** "Analytics" tab
2. **View performance metrics**:
   - Views, likes, comments, shares
   - Engagement rates
   - ROI calculations
   - Platform-specific insights

### Track Your Success

```bash
# Get analytics via API
curl -X GET http://localhost:5000/api/analytics/summary

# Response example:
{
  "total_content": 5,
  "total_views": 12500,
  "engagement_rate": "4.2%",
  "roi": "285%",
  "top_platform": "youtube"
}
```

---

## 🛠️ Next Steps & Advanced Features

### 🔄 **Automation Setup**

Enable automated content creation:

```bash
# Access N8N Workflows
open http://localhost:5678

# Import pre-built workflows
docker-compose exec n8n n8n import:workflow --file /data/workflows/auto-content-creation.json

# Schedule automatic trend monitoring every 6 hours
```

### 🎯 **Optimization Tips**

1. **Monitor trending topics** regularly for best opportunities
2. **A/B test different content styles** to find what works
3. **Use analytics data** to refine your content strategy
4. **Experiment with different AI models** for varying quality/cost

### 📈 **Scaling Up**

Ready for production? Check out:
- [🚀 Production Deployment Guide](../deployment/production.md)
- [⚙️ Advanced Configuration](../configuration.md)
- [🔒 Security Best Practices](../security.md)

---

## 🆘 Troubleshooting

### Common Issues & Solutions

#### ❌ **Docker Services Won't Start**
```bash
# Check Docker is running
docker --version
docker-compose --version

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop on Mac/Windows

# Reset and try again
docker-compose down -v
docker-compose up -d
```

#### ❌ **Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose exec postgres psql -U admin -d ai_content_factory_dev -c "SELECT version();"
```

#### ❌ **AI Services Not Working**
```bash
# Enable mock services for testing
echo "MOCK_AI_SERVICES=true" >> .env
docker-compose restart content-engine

# Check API keys are valid
curl -X POST http://localhost:5000/api/ai/test-connection
```

#### ❌ **Port Conflicts**
```bash
# Check what's using the ports
lsof -i :3000  # Dashboard
lsof -i :5000  # API
lsof -i :5678  # N8N

# Kill conflicting processes or change ports in docker-compose.yml
```

#### ❌ **Web Dashboard Not Loading**
```bash
# Check if the service is running
docker-compose ps web-dashboard

# Check logs
docker-compose logs web-dashboard

# Restart the service
docker-compose restart web-dashboard
```

### 🔧 **Performance Issues**

If the system feels slow:

```bash
# Check resource usage
docker stats

# Reduce concurrent processing
echo "MAX_CONCURRENT_GENERATIONS=2" >> .env
docker-compose restart

# Use budget tier for faster processing
echo "DEFAULT_QUALITY_TIER=budget" >> .env
```

### 📞 **Get Help**

Still stuck? We're here to help:

- 💬 **Discord**: [Join our community](https://discord.gg/aicontentfactory)
- 📧 **Email**: support@aicontentfactory.com  
- 📚 **Docs**: [Full documentation](https://docs.aicontentfactory.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/ai-content-factory/issues)

---

## 🎯 What's Next?

### 🌟 **Explore Advanced Features**

- **🤖 Custom AI Models**: Train models on your content style
- **📅 Content Scheduling**: Plan and schedule content in advance  
- **👥 Team Collaboration**: Invite team members and manage permissions
- **🎨 Brand Customization**: Apply your brand guidelines automatically
- **📊 Advanced Analytics**: Deep dive into performance metrics

### 📚 **Learn More**

- [📖 User Guide](user-guide.md) - Complete feature walkthrough
- [⚙️ Configuration Guide](configuration.md) - Customize everything
- [🔧 API Documentation](../api/) - Build custom integrations
- [🏗️ Architecture Guide](../architecture.md) - Understand the system

### 🚀 **Join the Community**

- Share your success stories
- Get inspiration from other creators
- Contribute to the project
- Request new features

---

## 🎉 Congratulations!

You've successfully set up AI Content Factory and created your first AI-generated content! 

**You're now ready to:**
- ✅ Scale your content creation process
- ✅ Leverage AI for consistent, high-quality content
- ✅ Automate your social media presence
- ✅ Focus on strategy while AI handles execution

---

<div align="center">

## 🌟 **Happy Content Creating!**

**Ready to revolutionize your content strategy?**

[🚀 Upgrade to Premium](https://aicontentfactory.com/pricing) • 
[💬 Join Community](https://discord.gg/aicontentfactory) • 
[📖 Full Documentation](https://docs.aicontentfactory.com)

---

**Need help?** We're just a message away: support@aicontentfactory.com

</div>

---

## 📊 Quick Reference

### 🔗 **Important URLs**
- Dashboard: http://localhost:3000
- API: http://localhost:5000
- N8N: http://localhost:5678
- Health Check: http://localhost:5000/health

### ⌨️ **Useful Commands**
```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Update system
git pull && docker-compose build && docker-compose up -d
```

### 🏷️ **Default Credentials**
- N8N: admin / admin
- Database: admin / dev_password
- Redis: (no password in development)

---

**🎯 Pro Tip**: Bookmark this page for quick reference during your AI content creation journey!