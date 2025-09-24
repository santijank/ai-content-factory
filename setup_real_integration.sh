# ai-content-factory/setup_real_integration.sh

#!/bin/bash

echo "🚀 Setting up Real Data Integration"
echo "=================================="

# Step 1: Install additional Python dependencies
echo "📦 Installing Python dependencies..."
pip install google-api-python-client>=2.100.0
pip install pytrends>=4.9.2
pip install openai>=1.0.0
pip install groq>=0.4.0
pip install aiofiles>=23.0.0
pip install asyncpg>=0.28.0

# Step 2: Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# YouTube Data API v3 (Get from Google Cloud Console)
YOUTUBE_API_KEY=your_youtube_api_key_here

# AI Services (Already provided)
GROQ_API_KEY=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
OPENAI_API_KEY=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

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/content_factory

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
ENABLE_METRICS=true
EOF
    echo "✅ .env file created. Please update with your YouTube API key."
else
    echo "✅ .env file already exists"
fi

# Step 3: Update requirements.txt
echo "📋 Updating requirements.txt..."
cat >> requirements.txt << 'EOF'

# Real Data Integration Dependencies
google-api-python-client>=2.100.0
pytrends>=4.9.2
openai>=1.0.0
groq>=0.4.0
aiofiles>=23.0.0
asyncpg>=0.28.0
aioredis>=2.0.0
EOF

# Step 4: Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs
mkdir -p data

# Step 5: Set up database migrations for real data
echo "🗃️ Updating database schema..."
cat > database/migrations/006_real_data_integration.sql << 'EOF'
-- Enhanced schema for real data integration
ALTER TABLE trends ADD COLUMN IF NOT EXISTS api_quota_cost INTEGER DEFAULT 0;
ALTER TABLE trends ADD COLUMN IF NOT EXISTS collection_method VARCHAR(50) DEFAULT 'api';
ALTER TABLE trends ADD COLUMN IF NOT EXISTS trend_velocity FLOAT DEFAULT 0.0;

-- Index for better performance
CREATE INDEX IF NOT EXISTS idx_trends_source_collected ON trends(source, collected_at);
CREATE INDEX IF NOT EXISTS idx_trends_popularity ON trends(popularity_score DESC);

-- AI analysis results table
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trend_id UUID REFERENCES trends(id),
    analysis_type VARCHAR(50) NOT NULL,
    viral_potential INTEGER,
    content_saturation INTEGER, 
    audience_interest INTEGER,
    monetization_opportunity INTEGER,
    overall_score FLOAT,
    reasoning TEXT,
    content_angles JSONB,
    api_cost DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(50) NOT NULL,
    endpoint VARCHAR(100),
    quota_used INTEGER DEFAULT 0,
    cost_estimate DECIMAL(10,4),
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_service_date ON api_usage_log(service_name, created_at);
CREATE INDEX IF NOT EXISTS idx_performance_type_date ON performance_metrics(metric_type, recorded_at);
EOF

# Step 6: Create configuration files
echo "⚙️ Creating configuration files..."

# Main config
cat > config/real_integration.yaml << 'EOF'
# Real Data Integration Configuration

# API Rate Limits (per day)
rate_limits:
  youtube:
    quota_limit: 9000
    requests_per_hour: 100
  google_trends:
    requests_per_hour: 100
  groq:
    requests_per_day: 14400  # Free tier
  openai:
    requests_per_minute: 60  # Tier 1

# Data Collection Settings
collection:
  youtube:
    default_region: "TH"
    max_results: 50
    categories: [1, 10, 15, 17, 20, 22, 23, 24, 25, 27, 28]
  google_trends:
    default_geo: "TH"
    timeframe: "today 7-d"
    batch_size: 5

# AI Analysis Settings
ai_analysis:
  groq:
    model: "llama3-8b-8192"
    temperature: 0.3
    max_tokens: 1000
  openai:
    model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 1500

# Pipeline Settings
pipeline:
  schedule: "0 */6 * * *"  # Every 6 hours
  max_trends_per_run: 30
  ai_analysis_limit: 15
  timeout_seconds: 300
EOF

# Monitoring config
cat > config/monitoring.yaml << 'EOF'
# Monitoring Configuration

# Metrics to track
metrics:
  - api_response_times
  - quota_usage_percentage
  - trends_collected_per_hour
  - opportunities_generated_per_hour
  - pipeline_success_rate
  - content_quality_scores

# Alerts
alerts:
  quota_threshold: 80  # Alert when 80% quota used
  error_rate_threshold: 10  # Alert when error rate > 10%
  pipeline_failure_notify: true

# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_file_size: "10MB"
  backup_count: 5
EOF

# Step 7: Create Docker configuration for real integration
echo "🐳 Creating Docker configuration..."
cat > Dockerfile.real << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Create necessary directories
RUN mkdir -p logs data

# Environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from real_integration_main import RealContentFactory; print('OK')" || exit 1

# Default command
CMD ["python", "real_integration_main.py"]
EOF

# Step 8: Create monitoring dashboard
echo "📊 Creating monitoring dashboard..."
mkdir -p monitoring/real_time
cat > monitoring/real_time/dashboard.py << 'EOF'
# Real-time monitoring dashboard for real integration
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

class RealTimeMonitor:
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # API usage in last hour
            cur.execute("""
                SELECT service_name, COUNT(*) as calls, 
                       AVG(response_time_ms) as avg_response_time,
                       SUM(quota_used) as total_quota
                FROM api_usage_log 
                WHERE created_at > NOW() - INTERVAL '1 hour'
                GROUP BY service_name
            """)
            api_usage = cur.fetchall()
            
            # Recent trends count
            cur.execute("""
                SELECT source, COUNT(*) as count
                FROM trends 
                WHERE collected_at > NOW() - INTERVAL '24 hours'
                GROUP BY source
            """)
            trend_counts = cur.fetchall()
            
            # Top opportunities
            cur.execute("""
                SELECT suggested_angle, priority_score, estimated_roi
                FROM content_opportunities 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY priority_score DESC
                LIMIT 10
            """)
            top_opportunities = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "api_usage": [dict(row) for row in api_usage],
                "trend_counts": [dict(row) for row in trend_counts],
                "top_opportunities": [dict(row) for row in top_opportunities]
            }
            
        except Exception as e:
            return {"error": str(e)}

# Usage: python monitoring/real_time/dashboard.py
if __name__ == "__main__":
    import os
    monitor = RealTimeMonitor(os.getenv("DATABASE_URL"))
    stats = asyncio.run(monitor.get_real_time_stats())
    print(json.dumps(stats, indent=2, default=str))
EOF

# Step 9: Create test script
echo "🧪 Creating test script..."
cat > test_real_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Real Data Integration
Run this to verify everything is working correctly.
"""

import asyncio
import os
from real_integration_main import test_real_integration, load_config

async def main():
    print("🔧 Testing Real Data Integration Setup")
    print("=" * 50)
    
    # Test 1: Check configuration
    print("1. Checking configuration...")
    config = load_config()
    
    required_keys = ["groq_api_key", "openai_api_key"]
    missing = [key for key in required_keys if not config.get(key)]
    
    if missing:
        print(f"❌ Missing required keys: {missing}")
        return False
    else:
        print("✅ Configuration OK")
    
    # Test 2: Check optional YouTube API
    if config.get("youtube_api_key"):
        print("✅ YouTube API key configured")
    else:
        print("⚠️  YouTube API key not configured (using mock data)")
    
    # Test 3: Run integration test
    print("\n2. Running integration test...")
    try:
        await test_real_integration()
        print("✅ Integration test completed")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Real Data Integration setup completed successfully!")
        print("\nNext steps:")
        print("1. Get YouTube API key from Google Cloud Console")
        print("2. Update .env file with your YouTube API key")
        print("3. Run: python real_integration_main.py")
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")
EOF

chmod +x test_real_integration.py

echo ""
echo "✅ Real Data Integration setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Update .env file with your YouTube API key"
echo "2. Run: python test_real_integration.py"
echo "3. If tests pass, run: python real_integration_main.py"
echo ""
echo "📖 Documentation:"
echo "- See docs/real-integration-guide.md for detailed setup"
echo "- Monitor logs in ./logs/ directory"
echo "- Check real-time stats: python monitoring/real_time/dashboard.py"
echo ""