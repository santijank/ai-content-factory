#!/bin/bash
# n8n-workflows/import-workflows.sh
# Auto-import script for N8N workflows

echo "🚀 Importing AI Content Factory N8N Workflows..."

# Check if n8n is running
if ! curl -s http://localhost:5678/healthz > /dev/null; then
    echo "❌ N8N is not running. Please start n8n first with: n8n start"
    exit 1
fi

echo "✅ N8N is running"

# Import workflows using N8N CLI
echo "📥 Importing workflows..."

# Function to import a workflow
import_workflow() {
    local workflow_file=$1
    local workflow_name=$2
    
    echo "Importing $workflow_name..."
    
    # Using N8N API to import workflow
    curl -X POST "http://localhost:5678/rest/workflows/import" \
         -H "Content-Type: application/json" \
         -d @"$workflow_file" \
         --silent --output /dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ $workflow_name imported successfully"
    else
        echo "❌ Failed to import $workflow_name"
    fi
}

# Import each workflow file
import_workflow "master-workflow.json" "Master Workflow"
import_workflow "trend-collection-workflow.json" "Trend Collection"
import_workflow "content-generation-workflow.json" "Content Generation"
import_workflow "platform-upload-workflow.json" "Platform Upload"
import_workflow "performance-monitoring-workflow.json" "Performance Monitoring"

echo ""
echo "🎉 Workflow import completed!"
echo ""
echo "📋 Next steps:"
echo "1. Access N8N at http://localhost:5678"
echo "2. Configure credentials for each service"
echo "3. Update webhook URLs if needed"
echo "4. Test each workflow individually"
echo "5. Activate workflows"
echo ""
echo "🔑 Default N8N credentials:"
echo "   Username: admin"
echo "   Password: (check your .env file)"

---

# n8n-workflows/README.md
# N8N Workflows for AI Content Factory

This directory contains all N8N workflow definitions for the AI Content Factory system.

## 📁 Workflow Files

| File | Description | Trigger |
|------|-------------|---------|
| `master-workflow.json` | Main orchestration workflow | Cron (6:00, 12:00, 18:00) |
| `trend-collection-workflow.json` | Collects trends from multiple sources | Webhook |
| `content-generation-workflow.json` | Generates content from opportunities | Webhook |
| `platform-upload-workflow.json` | Uploads content to platforms | Webhook |
| `performance-monitoring-workflow.json` | Monitors content performance | Cron (every 30 min) |

## 🚀 Quick Setup

### 1. Start N8N
```bash
# Install n8n globally
npm install n8n -g

# Start n8n
n8n start

# Access at http://localhost:5678
```

### 2. Import Workflows
```bash
# Option 1: Use the auto-import script
chmod +x import-workflows.sh
./import-workflows.sh

# Option 2: Manual import via N8N UI
# 1. Open N8N at http://localhost:5678
# 2. Click "Import from file" 
# 3. Upload each JSON file
```

### 3. Configure Credentials

#### Database Connection
- **Name**: `AI Factory Database`
- **Type**: PostgreSQL
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `ai_content_factory`
- **Username**: `postgres`
- **Password**: `your_password`

#### API Endpoints
Update these URLs in each workflow if different:
- **Main API**: `http://localhost:8000/api`
- **Trend Monitor**: `http://localhost:8001/api`
- **Content Engine**: `http://localhost:8002/api`
- **Platform Manager**: `http://localhost:8003/api`

### 4. Set Webhook URLs

Make sure these webhook URLs are accessible:
- `http://localhost:5678/webhook/collect-trends`
- `http://localhost:5678/webhook/create-content`
- `http://localhost:5678/webhook/upload-content`
- `http://localhost:5678/webhook/opportunities-ready`
- `http://localhost:5678/webhook/content-ready`
- `http://localhost:5678/webhook/upload-complete`

## 🔄 Workflow Details

### Master Workflow
- **Purpose**: Orchestrates the entire content creation process
- **Schedule**: Runs 3 times daily (06:00, 12:00, 18:00 UTC)
- **Flow**: Health Check → Trend Collection → Opportunity Generation → Notifications

### Trend Collection Workflow  
- **Purpose**: Collects trends from YouTube, Google, Twitter, Reddit
- **Trigger**: Webhook from master workflow or manual trigger
- **Flow**: Multi-source Collection → AI Analysis → Filtering → Opportunity Generation

### Content Generation Workflow
- **Purpose**: Creates content from selected opportunities
- **Trigger**: User selection via webhook
- **Flow**: Validation → Content Planning → Asset Generation → Storage

### Platform Upload Workflow
- **Purpose**: Uploads content to multiple platforms
- **Trigger**: Manual or automatic after content creation
- **Flow**: Content Retrieval → Platform Routing → Upload → Result Storage

### Performance Monitoring Workflow
- **Purpose**: Tracks content performance and sends alerts
- **Schedule**: Every 30 minutes
- **Flow**: Get Active Content → Platform Analytics → Store Metrics → Generate Alerts

## 🧪 Testing Workflows

### Test Individual Workflows
```bash
# Test trend collection
curl -X POST http://localhost:5678/webhook/collect-trends

# Test content creation  
curl -X POST http://localhost:5678/webhook/create-content \
  -H "Content-Type: application/json" \
  -d '{"opportunity_id": "test-uuid", "quality_tier": "balanced"}'

# Test upload
curl -X POST http://localhost:5678/webhook/upload-content \
  -H "Content-Type: application/json" \
  -d '{"content_id": "test-uuid", "platforms": ["youtube"]}'
```

### Monitor Workflow Executions
1. Open N8N interface at `http://localhost:5678`
2. Go to "Executions" tab
3. Monitor workflow runs and debug any issues

## ⚙️ Customization

### Modify Scheduling
Edit the cron expressions in workflow files:
```json
"parameters": {
  "triggerTimes": {
    "item": [
      {
        "hour": 6,    // Change hours here
        "minute": 0
      }
    ]
  }
}
```

### Add New Platforms
1. Add new HTTP request node for the platform
2. Update the platform router/switch node
3. Add connection to merge node
4. Update platform-specific configurations

### Custom Error Handling
Each workflow includes error handling nodes. Customize:
- Retry policies
- Error notifications  
- Fallback actions
- Log levels

## 🔐 Security Notes

- Use environment variables for sensitive data
- Enable N8N authentication in production
- Secure webhook endpoints
- Use HTTPS in production
- Regularly update N8N version

## 📊 Monitoring

### Workflow Health
- Monitor execution success rates
- Set up alerts for failed workflows
- Check execution time trends
- Monitor resource usage

### Integration with Main System
The workflows integrate with:
- Main API at `localhost:8000`
- Database for storing results
- External AI services
- Platform APIs
- Notification systems

## 🆘 Troubleshooting

### Common Issues

**Workflow not triggering:**
- Check if workflow is active
- Verify webhook URLs
- Check N8N logs

**Database connection failed:**
- Verify PostgreSQL is running
- Check credentials in N8N
- Test connection manually

**API timeouts:**
- Increase timeout values
- Check service availability
- Monitor resource usage

**Import failed:**
- Check JSON syntax
- Verify N8N version compatibility
- Try manual import via UI

### Debug Mode
Enable debug logging in N8N:
```bash
export N8N_LOG_LEVEL=debug
n8n start
```

## 📞 Support

For issues with workflows:
1. Check N8N execution logs
2. Verify all services are running
3. Test individual nodes
4. Check the main system logs
5. Refer to N8N documentation

---

**Created for AI Content Factory v1.0**  
**Last Updated: January 2024**