# Local Development Setup Guide

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up the AI Content Factory locally, ensure you have the following installed:

### Required Software
- **Git**: Version control
- **Docker**: Container runtime (v20.10+)
- **Docker Compose**: Multi-container orchestration (v2.0+)
- **Python**: 3.9 or higher
- **Node.js**: 16+ (for web dashboard)
- **PostgreSQL Client**: For database management (optional)

### API Keys (Required for Full Functionality)
- **YouTube Data API v3**: For trend collection
- **Twitter API v2**: For Twitter trends
- **OpenAI API**: For AI content generation (optional)
- **Groq API**: Budget AI option
- **Google Trends API**: Unofficial API access

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

## Quick Start

The fastest way to get started is using our automated setup script:

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/ai-content-factory.git
cd ai-content-factory
```

### 2. Run Setup Script
```bash
# Make script executable
chmod +x scripts/setup.sh

# Run setup (will install everything)
./scripts/setup.sh
```

### 3. Access the Application
After setup completes, access these URLs:
- **Main Dashboard**: http://localhost:5000
- **Web Dashboard**: http://localhost:3000
- **N8N Workflows**: http://localhost:5678
- **Monitoring**: http://localhost:9090

### 4. Default Credentials
- **N8N**: admin / (check .env file for password)
- **Database**: admin / (check .env file for password)

## Manual Setup

If you prefer manual setup or the script fails:

### 1. Clone and Prepare Environment
```bash
git clone https://github.com/your-org/ai-content-factory.git
cd ai-content-factory

# Copy environment template
cp .env.example .env

# Create data directories
mkdir -p data/{postgres,n8n,uploads,logs}
```

### 2. Configure Environment Variables
Edit `.env` file with your settings:

```bash
# Database Configuration
POSTGRES_DB=content_factory
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Keys
YOUTUBE_API_KEY=your_youtube_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# N8N Configuration
N8N_PASSWORD=your_n8n_password
N8N_ENCRYPTION_KEY=your_encryption_key

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=your_secret_key
```

### 3. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Node.js Environment (Optional)
```bash
cd web-dashboard
npm install
cd ..
```

### 5. Start Infrastructure Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready
sleep 10
```

### 6. Initialize Database
```bash
# Run migrations
python database/migrate.py migrate

# Optional: Seed with sample data
python database/migrate.py seed
```

### 7. Start Application Services
```bash
# Option A: Use Docker Compose (Recommended)
docker-compose up -d

# Option B: Start services individually
python trend-monitor/app.py &
python content-engine/app.py &
python platform-manager/app.py &
python monitoring/app.py &

# Start web dashboard (if using Node.js)
cd web-dashboard && npm start &
```

## Configuration

### Environment Configuration
The system uses environment-specific configuration files:

```bash
config/
├── app_config.yaml       # Main application config
├── ai_models.yaml        # AI service configurations
├── quality_tiers.yaml    # Service quality tiers
└── platform_configs/     # Platform-specific settings
    ├── youtube.yaml
    ├── tiktok.yaml
    ├── instagram.yaml
    └── facebook.yaml
```

### Quality Tiers
Configure different AI service tiers in `config/quality_tiers.yaml`:

```yaml
budget:
  text_ai: "groq"
  image_ai: "stable_diffusion_local"
  audio_ai: "gtts"
  cost_per_content: 0.05

balanced:
  text_ai: "openai"
  image_ai: "leonardo_ai"
  audio_ai: "azure_tts"
  cost_per_content: 0.25

premium:
  text_ai: "claude"
  image_ai: "midjourney"
  audio_ai: "elevenlabs"
  cost_per_content: 1.50
```

### Platform Configuration
Configure upload settings for each platform:

```yaml
# config/platform_configs/youtube.yaml
youtube:
  api_quota_per_day: 10000
  max_video_size: "128MB"
  supported_formats: ["mp4", "avi", "mov"]
  default_privacy: "private"
  auto_tags: true
  seo_optimization: true
```

## Development Workflow

### 1. Code Structure
```
ai-content-factory/
├── trend-monitor/          # Trend collection service
├── content-engine/         # AI content generation
├── platform-manager/      # Upload management
├── web-dashboard/          # React frontend
├── database/              # Database schemas and migrations
├── shared/                # Shared utilities and models
├── tests/                 # Test suites
├── config/                # Configuration files
├── scripts/               # Automation scripts
└── kubernetes/            # Deployment manifests
```

### 2. Making Changes

#### Backend Services
```bash
# Make changes to Python code
# The services auto-reload in development mode

# Run specific service for debugging
cd content-engine
python app.py

# View logs
docker-compose logs -f content-engine
```

#### Frontend Development
```bash
cd web-dashboard

# Start development server with hot reload
npm start

# Build for production
npm run build
```

#### Database Changes
```bash
# Create new migration
cd database
python migrate.py create "your_migration_name"

# Apply migrations
python migrate.py migrate

# Rollback if needed
python migrate.py rollback
```

### 3. Adding New Features

#### New Trend Source
1. Create new collector in `trend-monitor/services/`
2. Add to `TrendCollector` class
3. Update database schema if needed
4. Add tests

#### New AI Service
1. Create service class in `content-engine/ai_services/`
2. Implement base interface
3. Add to `ServiceRegistry`
4. Update configuration

#### New Platform
1. Create uploader in `platform-manager/services/uploaders/`
2. Implement upload interface
3. Add platform configuration
4. Update UI

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_trend_collector.py
```

### Test Configuration
Create test-specific environment:
```bash
cp .env .env.test

# Modify .env.test for testing
DB_NAME=content_factory_test
ENVIRONMENT=test
```

### Writing Tests
```python
# tests/unit/test_trend_collector.py
import pytest
from trend_monitor.services.trend_collector import TrendCollector

class TestTrendCollector:
    @pytest.fixture
    def collector(self):
        return TrendCollector()
    
    async def test_collect_trends(self, collector):
        result = await collector.collect_trends()
        assert len(result) > 0
        assert all('topic' in trend for trend in result)
```

### Integration Testing
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Development Tools

### Useful Commands
```bash
# View all services status
docker-compose ps

# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f trend-monitor

# Restart a service
docker-compose restart content-engine

# Access database
docker-compose exec postgres psql -U admin -d content_factory

# Access Redis
docker-compose exec redis redis-cli

# Shell into a container
docker-compose exec trend-monitor bash
```

### Database Management
```bash
# Database migrations
./scripts/migrate.sh migrate

# Create backup
./scripts/backup.sh backup

# Restore from backup
./scripts/backup.sh restore backup_name

# Reset database (development only)
./scripts/migrate.sh reset
```

### Debugging

#### Python Services
```python
# Add debugging breakpoints
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Enable debug logging
export LOG_LEVEL=DEBUG
```

#### API Debugging
```bash
# Test API endpoints
curl -X GET http://localhost:8001/health

# Test with authentication
curl -X GET http://localhost:8001/trends \
  -H "Authorization: Bearer your_token"
```

### IDE Setup

#### VS Code Configuration
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

#### PyCharm Configuration
1. Set Python interpreter to `./venv/bin/python`
2. Mark `src/` as sources root
3. Configure pytest as default test runner
4. Enable Docker integration

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using port 5000
lsof -i :5000

# Kill process using port
kill -9 $(lsof -t -i :5000)

# Use different ports in .env
MAIN_APP_PORT=5001
WEB_DASHBOARD_PORT=3001
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U admin -d content_factory -c "SELECT 1;"

# Reset database container
docker-compose down postgres
docker-compose up -d postgres
```

#### Service Not Starting
```bash
# Check service logs
docker-compose logs service-name

# Check if all dependencies are running
docker-compose ps

# Rebuild service
docker-compose build service-name
docker-compose up -d service-name
```

#### API Key Issues
```bash
# Verify API keys are set
env | grep API_KEY

# Test API key validity
curl -H "Authorization: Bearer $YOUTUBE_API_KEY" \
  "https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key=$YOUTUBE_API_KEY"
```

#### Memory Issues
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Clean up unused containers and images
docker system prune -a
```

### Performance Optimization

#### Local Development
```bash
# Use local Redis instead of Docker
# Comment out Redis in docker-compose.yml
# Install Redis locally: brew install redis (macOS)

# Use environment-specific configs
export ENVIRONMENT=development

# Enable debug mode for detailed logs
export DEBUG=true
```

#### Faster Rebuilds
```bash
# Use Docker build cache
docker-compose build --parallel

# Use .dockerignore to exclude unnecessary files
echo "node_modules\n*.pyc\n__pycache__" > .dockerignore
```

### Getting Help

#### Log Analysis
```bash
# Aggregate logs from all services
docker-compose logs > debug.log

# Search for errors
grep -i error debug.log

# Filter by service and time
docker-compose logs --since="1h" trend-monitor
```

#### Health Checks
```bash
# Check all service health
curl http://localhost:5000/health
curl http://localhost:8001/health  # Trend Monitor
curl http://localhost:8002/health  # Content Engine
curl http://localhost:8003/health  # Platform Manager
```

#### System Information
```bash
# Generate system report for debugging
./scripts/debug-info.sh > system-report.txt
```

### Next Steps

After successful local setup:

1. **Explore the Dashboard**: Visit http://localhost:5000 to see the main interface
2. **Configure API Keys**: Add your API keys to `.env` for full functionality
3. **Run First Collection**: Trigger trend collection from the dashboard
4. **Generate Sample Content**: Create your first AI-generated content
5. **Set Up Platform Connections**: Configure social media platform credentials

For production deployment, see [Docker Setup Guide](docker-setup.md) or [Kubernetes Setup Guide](kubernetes-setup.md).

---

Happy coding! 🚀