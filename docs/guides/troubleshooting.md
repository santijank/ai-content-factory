# AI Content Factory - Troubleshooting Guide

## 📋 Table of Contents
- [Quick Diagnostic](#quick-diagnostic)
- [Common Issues](#common-issues)
- [Service-Specific Problems](#service-specific-problems)
- [Performance Issues](#performance-issues)
- [API & Integration Problems](#api--integration-problems)
- [Data & Database Issues](#data--database-issues)
- [Deployment Problems](#deployment-problems)
- [Error Code Reference](#error-code-reference)
- [Advanced Debugging](#advanced-debugging)
- [Getting Help](#getting-help)

## Quick Diagnostic

### 🚀 Start Here - Basic Health Check

Run this command to check overall system health:

```bash
# Quick system status check
curl -s http://localhost:5000/health | jq '.'

# Or use the built-in diagnostic script
./scripts/health-check.sh
```

**Expected Output:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "trend_monitor": "healthy",
    "content_engine": "healthy",
    "platform_manager": "healthy"
  },
  "timestamp": "2024-09-15T10:30:00Z"
}
```

### 🔍 Identify Your Issue Category

| Symptom | Category | Quick Fix |
|---------|----------|-----------|
| Services won't start | [Deployment](#deployment-problems) | Check Docker/dependencies |
| Slow/hanging operations | [Performance](#performance-issues) | Check resources/logs |
| API calls failing | [API Integration](#api--integration-problems) | Verify keys/connectivity |
| Data not updating | [Database](#data--database-issues) | Check DB connection |
| Trends not collecting | [Trend Monitor](#trend-monitor-issues) | Check API quotas |
| Content not generating | [Content Engine](#content-engine-issues) | Check AI service status |
| Uploads failing | [Platform Manager](#platform-manager-issues) | Verify platform auth |

## Common Issues

### 🐳 Docker & Container Issues

#### Issue: "docker-compose up" fails
**Symptoms:**
- Services fail to start
- Port conflicts
- Volume mounting errors

**Diagnosis:**
```bash
# Check Docker daemon
docker --version
docker info

# Check for port conflicts
lsof -i :5000 -i :5432 -i :6379

# Check Docker Compose file syntax
docker-compose config
```

**Solutions:**
```bash
# 1. Clean up existing containers
docker-compose down -v
docker system prune -f

# 2. Check available ports
./scripts/check-ports.sh

# 3. Rebuild containers
docker-compose build --no-cache
docker-compose up -d

# 4. If still failing, check logs
docker-compose logs
```

#### Issue: Container exits immediately
**Symptoms:**
- Container starts then stops
- Exit code 1 or 125
- No application logs

**Diagnosis:**
```bash
# Check container logs
docker-compose logs [service-name]

# Check exit codes
docker-compose ps

# Run container interactively
docker-compose run --rm [service-name] bash
```

**Solutions:**
```bash
# 1. Check environment variables
cat .env
grep -v "^#" .env | grep -v "^$"

# 2. Verify file permissions
ls -la data/
chmod -R 755 data/

# 3. Check Docker resources
docker system df
docker stats
```

### 🔗 Network & Connectivity Issues

#### Issue: Services can't communicate
**Symptoms:**
- "Connection refused" errors
- Timeouts between services
- API calls failing

**Diagnosis:**
```bash
# Check network connectivity
docker-compose exec trend-monitor ping postgres
docker-compose exec content-engine ping redis

# Check service resolution
docker-compose exec trend-monitor nslookup postgres
```

**Solutions:**
```bash
# 1. Restart Docker network
docker-compose down
docker network prune
docker-compose up -d

# 2. Check service dependencies
docker-compose ps
docker-compose logs postgres
docker-compose logs redis

# 3. Verify service ports
docker-compose port postgres 5432
docker-compose port redis 6379
```

### 🔑 Authentication & API Key Issues

#### Issue: API keys not working
**Symptoms:**
- "Unauthorized" errors
- "Invalid API key" messages
- Quota exceeded warnings

**Diagnosis:**
```bash
# Check environment variables
echo $YOUTUBE_API_KEY
echo $OPENAI_API_KEY
echo $GROQ_API_KEY

# Test API keys directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check quota usage
./scripts/check-api-quotas.sh
```

**Solutions:**
```bash
# 1. Verify API keys in .env
grep "API_KEY" .env

# 2. Re-generate keys if needed
# Visit respective API provider websites

# 3. Restart services to pick up new keys
docker-compose restart

# 4. Check API provider status pages
curl -s https://status.openai.com/api/v2/summary.json
```

## Service-Specific Problems

### 📊 Trend Monitor Issues

#### Issue: No trends being collected
**Symptoms:**
- Empty trends dashboard
- "No data available" messages
- Stale trend data

**Diagnosis:**
```bash
# Check trend monitor logs
docker-compose logs trend-monitor

# Test trend collection manually
curl -X POST http://localhost:8001/trends/collect \
  -H "Authorization: Bearer $JWT_TOKEN"

# Check database for trends
docker-compose exec postgres psql -U admin -d content_factory \
  -c "SELECT COUNT(*) FROM trends WHERE collected_at > NOW() - INTERVAL '1 hour';"
```

**Solutions:**
```bash
# 1. Check API keys and quotas
./scripts/check-api-keys.sh

# 2. Manually trigger collection
curl -X POST http://localhost:8001/trends/collect

# 3. Check N8N workflow status
curl http://localhost:5678/webhook/test

# 4. Restart trend monitor
docker-compose restart trend-monitor
```

#### Issue: Duplicate trends being created
**Symptoms:**
- Same trends appearing multiple times
- Database growing too fast
- Performance degradation

**Diagnosis:**
```bash
# Check for duplicates
docker-compose exec postgres psql -U admin -d content_factory -c "
SELECT topic, COUNT(*) 
FROM trends 
GROUP BY topic 
HAVING COUNT(*) > 1 
ORDER BY COUNT(*) DESC;
"
```

**Solutions:**
```bash
# 1. Run deduplication script
python scripts/deduplicate-trends.py

# 2. Check deduplication logic
grep -n "deduplicate" trend-monitor/services/trend_collector.py

# 3. Add unique constraints
./scripts/migrate.sh add_unique_constraints
```

### 🤖 Content Engine Issues

#### Issue: Content generation fails
**Symptoms:**
- "Generation failed" errors
- Incomplete content pieces
- AI service timeouts

**Diagnosis:**
```bash
# Check content engine logs
docker-compose logs content-engine | grep -i error

# Test AI services individually
curl -X POST http://localhost:8002/ai/text/test
curl -X POST http://localhost:8002/ai/image/test
curl -X POST http://localhost:8002/ai/audio/test

# Check service registry status
curl http://localhost:8002/services/status
```

**Solutions:**
```bash
# 1. Check AI service API keys
grep -E "(OPENAI|GROQ|CLAUDE)" .env

# 2. Test service connectivity
ping api.openai.com
ping api.groq.com

# 3. Lower quality tier temporarily
export QUALITY_TIER=budget
docker-compose restart content-engine

# 4. Check service quotas
./scripts/check-ai-quotas.sh
```

#### Issue: Poor content quality
**Symptoms:**
- Generic or low-quality text
- Blurry or inappropriate images
- Robotic audio output

**Diagnosis:**
```bash
# Check current quality settings
curl http://localhost:8002/config/quality-tier

# Review recent content samples
curl http://localhost:8002/content/recent?limit=5

# Check AI service performance
curl http://localhost:8002/ai/performance-stats
```

**Solutions:**
```bash
# 1. Upgrade quality tier
export QUALITY_TIER=premium
docker-compose restart content-engine

# 2. Refine prompts and templates
# Edit files in content-engine/templates/

# 3. Check AI service status
curl https://status.openai.com/api/v2/status.json

# 4. Review and update prompts
./scripts/update-prompts.sh
```

### 📤 Platform Manager Issues

#### Issue: Upload failures
**Symptoms:**
- "Upload failed" notifications
- Content stuck in "uploading" status
- Platform authentication errors

**Diagnosis:**
```bash
# Check platform manager logs
docker-compose logs platform-manager | tail -50

# Test platform connections
curl http://localhost:8003/platforms/status

# Check individual platform auth
curl http://localhost:8003/platforms/youtube/auth-status
curl http://localhost:8003/platforms/tiktok/auth-status
```

**Solutions:**
```bash
# 1. Re-authenticate platforms
# Visit dashboard -> Settings -> Platforms -> Reconnect

# 2. Check platform API status
curl https://www.googleapis.com/youtube/v3/channels

# 3. Verify file formats and sizes
./scripts/check-content-compliance.sh

# 4. Restart platform manager
docker-compose restart platform-manager
```

#### Issue: Slow upload speeds
**Symptoms:**
- Uploads taking hours
- Frequent upload timeouts
- High network usage

**Diagnosis:**
```bash
# Check network speed
speedtest-cli

# Monitor upload progress
docker-compose logs -f platform-manager | grep upload

# Check disk I/O
iostat -x 1

# Monitor network usage
iftop
```

**Solutions:**
```bash
# 1. Compress content before upload
export ENABLE_COMPRESSION=true

# 2. Upload during off-peak hours
# Configure in Settings -> Upload Schedule

# 3. Increase upload timeout
export UPLOAD_TIMEOUT=3600  # 1 hour

# 4. Use wired connection if possible
```

## Performance Issues

### 🐌 Slow System Response

#### Issue: Dashboard loading slowly
**Symptoms:**
- Pages take >5 seconds to load
- API responses timing out
- Browser becoming unresponsive

**Diagnosis:**
```bash
# Check system resources
docker stats
htop

# Test API response times
time curl http://localhost:5000/api/trends

# Check database performance
docker-compose exec postgres psql -U admin -d content_factory -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
"
```

**Solutions:**
```bash
# 1. Restart services
docker-compose restart

# 2. Clear caches
docker-compose exec redis redis-cli FLUSHALL

# 3. Optimize database
./scripts/optimize-database.sh

# 4. Increase Docker resources
# Docker Desktop -> Settings -> Resources -> 8GB RAM
```

### 💾 Memory Issues

#### Issue: Out of memory errors
**Symptoms:**
- Containers getting killed
- "Cannot allocate memory" errors
- System becoming unresponsive

**Diagnosis:**
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check swap usage
swapon --show

# Identify memory-hungry processes
ps aux --sort=-%mem | head -10
```

**Solutions:**
```bash
# 1. Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory

# 2. Optimize container memory limits
# Edit docker-compose.yml memory limits

# 3. Enable swap if needed
sudo swapon /swapfile

# 4. Scale down services temporarily
docker-compose scale content-engine=1
```

### 💽 Disk Space Issues

#### Issue: No space left on device
**Symptoms:**
- "No space left on device" errors
- Database write failures
- Log files not updating

**Diagnosis:**
```bash
# Check disk usage
df -h
docker system df

# Find large files
du -sh /* | sort -rh | head -10

# Check Docker volume usage
docker volume ls
docker volume inspect [volume-name]
```

**Solutions:**
```bash
# 1. Clean up Docker resources
docker system prune -a --volumes

# 2. Rotate logs
./scripts/rotate-logs.sh

# 3. Clean up old backups
find backups/ -mtime +30 -delete

# 4. Compress old data
./scripts/compress-old-data.sh
```

## API & Integration Problems

### 🔌 External API Issues

#### Issue: API rate limits exceeded
**Symptoms:**
- "Rate limit exceeded" errors
- 429 HTTP status codes
- Delayed API responses

**Diagnosis:**
```bash
# Check current API usage
./scripts/check-api-usage.sh

# Review rate limit headers
curl -I https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check API logs
grep -i "rate.limit" logs/api.log
```

**Solutions:**
```bash
# 1. Implement exponential backoff
# Already built into most services

# 2. Distribute API calls across time
export API_RATE_LIMIT_DELAY=2  # seconds

# 3. Upgrade API plan if needed
# Visit API provider's pricing page

# 4. Use multiple API keys for rotation
# Configure in config/api_keys.yaml
```

#### Issue: Webhook delivery failures
**Symptoms:**
- Missing webhook notifications
- Delayed event processing
- Webhook timeout errors

**Diagnosis:**
```bash
# Check webhook logs
grep -i webhook logs/platform-manager.log

# Test webhook endpoint
curl -X POST http://localhost:8003/webhooks/test

# Check webhook queue
docker-compose exec redis redis-cli LLEN webhook_queue
```

**Solutions:**
```bash
# 1. Verify webhook URLs
curl -I $WEBHOOK_URL

# 2. Check firewall/network access
telnet $WEBHOOK_HOST $WEBHOOK_PORT

# 3. Increase webhook timeout
export WEBHOOK_TIMEOUT=30

# 4. Implement webhook retry logic
# Built into platform-manager service
```

## Data & Database Issues

### 🗄️ Database Connection Problems

#### Issue: Cannot connect to database
**Symptoms:**
- "Connection refused" errors
- "FATAL: password authentication failed"
- Services waiting for database

**Diagnosis:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection manually
docker-compose exec postgres psql -U admin -d content_factory -c "SELECT 1;"

# Check PostgreSQL logs
docker-compose logs postgres | tail -20
```

**Solutions:**
```bash
# 1. Restart PostgreSQL
docker-compose restart postgres

# 2. Check credentials
grep -E "(POSTGRES_|DB_)" .env

# 3. Reset PostgreSQL data
docker-compose down
docker volume rm ai-content-factory_postgres_data
docker-compose up -d postgres

# 4. Wait for database initialization
sleep 30
./scripts/migrate.sh migrate
```

### 📊 Data Corruption Issues

#### Issue: Inconsistent data
**Symptoms:**
- Trend counts don't match
- Missing foreign key references
- Duplicate primary keys

**Diagnosis:**
```bash
# Check data integrity
./scripts/check-data-integrity.sh

# Verify foreign key constraints
docker-compose exec postgres psql -U admin -d content_factory -c "
SELECT 
  tc.table_name, 
  tc.constraint_name,
  tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'FOREIGN KEY';
"

# Look for orphaned records
./scripts/find-orphaned-records.sh
```

**Solutions:**
```bash
# 1. Run data repair script
./scripts/repair-data.sh

# 2. Restore from backup
./scripts/backup.sh restore latest_backup

# 3. Re-import clean data
./scripts/clean-import.sh

# 4. Add missing constraints
./scripts/add-constraints.sh
```

## Deployment Problems

### ☸️ Kubernetes Issues

#### Issue: Pods not starting
**Symptoms:**
- Pods stuck in "Pending" state
- "ImagePullBackOff" errors
- Resource quota exceeded

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n ai-content-factory

# Describe problem pods
kubectl describe pod [pod-name] -n ai-content-factory

# Check events
kubectl get events -n ai-content-factory --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n ai-content-factory
```

**Solutions:**
```bash
# 1. Check image availability
docker pull ghcr.io/your-org/ai-content-factory/content-engine:latest

# 2. Verify resource requests/limits
kubectl get pods -n ai-content-factory -o yaml | grep -A 10 resources

# 3. Check node capacity
kubectl describe nodes

# 4. Scale down if needed
kubectl scale deployment content-engine --replicas=1 -n ai-content-factory
```

#### Issue: Service discovery problems
**Symptoms:**
- Services can't reach each other
- DNS resolution failures
- Connection timeouts

**Diagnosis:**
```bash
# Test service resolution
kubectl exec -it [pod-name] -n ai-content-factory -- nslookup postgres

# Check service endpoints
kubectl get endpoints -n ai-content-factory

# Test connectivity
kubectl exec -it [pod-name] -n ai-content-factory -- ping postgres
```

**Solutions:**
```bash
# 1. Check service definitions
kubectl get services -n ai-content-factory -o yaml

# 2. Verify selector labels
kubectl get pods --show-labels -n ai-content-factory

# 3. Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system

# 4. Check network policies
kubectl get networkpolicies -n ai-content-factory
```

### 🐋 Docker Compose Issues

#### Issue: Services dependency problems
**Symptoms:**
- Services starting before dependencies
- Database connection failures at startup
- Race condition errors

**Diagnosis:**
```bash
# Check service startup order
docker-compose logs | grep -E "(Starting|started|Waiting)"

# Test dependencies
docker-compose exec content-engine ping postgres
docker-compose exec trend-monitor ping redis
```

**Solutions:**
```bash
# 1. Add proper depends_on clauses
# Edit docker-compose.yml

# 2. Implement health checks
# Add healthcheck sections to services

# 3. Use wait scripts
docker-compose exec content-engine ./wait-for-postgres.sh

# 4. Restart in correct order
docker-compose down
docker-compose up -d postgres redis
sleep 10
docker-compose up -d
```

## Error Code Reference

### HTTP Error Codes

| Code | Service | Meaning | Solution |
|------|---------|---------|----------|
| 400 | API | Bad Request | Check request format |
| 401 | API | Unauthorized | Verify authentication |
| 403 | API | Forbidden | Check permissions |
| 404 | API | Not Found | Verify endpoint URL |
| 429 | API | Rate Limited | Wait and retry |
| 500 | API | Server Error | Check service logs |
| 502 | Proxy | Bad Gateway | Check upstream service |
| 503 | API | Service Unavailable | Service may be starting |
| 504 | Proxy | Gateway Timeout | Increase timeout |

### Application Error Codes

| Code | Service | Description | Action |
|------|---------|-------------|--------|
| TM001 | Trend Monitor | API quota exceeded | Check API limits |
| TM002 | Trend Monitor | Invalid API key | Update credentials |
| CE001 | Content Engine | AI service unavailable | Check AI service status |
| CE002 | Content Engine | Generation timeout | Increase timeout |
| PM001 | Platform Manager | Upload failed | Check platform auth |
| PM002 | Platform Manager | File too large | Compress content |
| DB001 | Database | Connection failed | Check database |
| DB002 | Database | Migration failed | Check migration logs |

### Custom Error Codes

```bash
# Look up error code details
./scripts/error-lookup.sh CE001

# Get recent errors
grep -E "CE001|TM001|PM001" logs/application.log | tail -10

# Error code statistics
./scripts/error-stats.sh
```

## Advanced Debugging

### 🔍 Log Analysis

#### Centralized Logging
```bash
# Aggregate all logs
docker-compose logs > all-services.log

# Search for specific errors
grep -i "error\|exception\|failed" all-services.log

# Filter by time range
docker-compose logs --since="1h" --until="30m"

# Follow logs in real-time
docker-compose logs -f -t
```

#### Log Parsing Scripts
```bash
# Parse API response times
./scripts/parse-api-times.sh

# Extract error patterns
./scripts/extract-errors.sh

# Generate log summary
./scripts/log-summary.sh
```

### 🧪 Testing & Validation

#### Health Check Scripts
```bash
# Comprehensive health check
./scripts/full-health-check.sh

# Service-specific tests
./scripts/test-trend-monitor.sh
./scripts/test-content-engine.sh
./scripts/test-platform-manager.sh

# End-to-end workflow test
./scripts/e2e-test.sh
```

#### Performance Testing
```bash
# Load test APIs
./scripts/load-test.sh

# Database performance test
./scripts/db-performance-test.sh

# Memory leak detection
./scripts/memory-test.sh

# Stress test content generation
./scripts/stress-test-generation.sh
```

### 🔧 System Debugging

#### Process Analysis
```bash
# Check running processes
ps aux | grep -E "(python|node|postgres|redis)"

# Monitor system calls
strace -p $(pgrep python)

# Check file descriptors
lsof -p $(pgrep python)

# Network connections
netstat -tulpn | grep -E "(5000|5432|6379)"
```

#### Resource Monitoring
```bash
# Real-time resource usage
watch -n 1 'docker stats --no-stream'

# Historical resource data
./scripts/resource-history.sh

# Disk I/O monitoring
iotop -a

# Network traffic analysis
./scripts/network-analysis.sh
```

## Getting Help

### 📝 Information to Gather

Before seeking help, collect this information:

#### System Information
```bash
# Generate system report
./scripts/system-report.sh > system-info.txt

# Include the following:
# - Operating system and version
# - Docker and Docker Compose versions
# - Available system resources
# - Network configuration
# - Current error messages
```

#### Application State
```bash
# Service status
docker-compose ps > service-status.txt

# Recent logs
docker-compose logs --tail=100 > recent-logs.txt

# Configuration (sanitized)
grep -v "PASSWORD\|SECRET\|KEY" .env > config-sanitized.txt

# Database status
./scripts/db-status.sh > db-status.txt
```

### 🎫 Support Channels

#### Community Support
- **GitHub Issues**: https://github.com/your-org/ai-content-factory/issues
- **Discord Server**: https://discord.gg/ai-content-factory
- **Stack Overflow**: Tag questions with `ai-content-factory`

#### Professional Support
- **Email**: support@ai-content-factory.com
- **Priority Support**: Available for enterprise customers
- **Emergency Hotline**: For production outages

#### Self-Help Resources
- **Documentation**: https://docs.ai-content-factory.com
- **Video Tutorials**: https://youtube.com/ai-content-factory
- **Knowledge Base**: https://help.ai-content-factory.com

### 📧 Effective Support Requests

#### Email Template
```
Subject: [URGENT/HIGH/MEDIUM/LOW] Brief description of issue

Environment: [Production/Staging/Development]
Version: [Release version or commit hash]
Affected Services: [List of services having issues]

Problem Description:
[Detailed description of what you were trying to do and what happened]

Steps to Reproduce:
1. [First step]
2. [Second step]
3. [Result]

Expected Behavior:
[What should have happened]

Actual Behavior:
[What actually happened]

Error Messages:
[Exact error messages, stack traces, or log entries]

Troubleshooting Attempted:
[What you've already tried]

System Information:
[Attach system-info.txt]

Additional Context:
[Any other relevant information]
```

### 🔄 Escalation Process

1. **Self-diagnosis** using this guide (15-30 minutes)
2. **Community forums** for common issues
3. **Email support** for specific problems
4. **Priority support** for urgent issues (enterprise)
### 🛠️ Debug Mode Activation

For developers and advanced users:

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services with debug logging
docker-compose restart

# Enable profiling
export ENABLE_PROFILING=true

# Enable SQL query logging
export LOG_SQL_QUERIES=true

# Enable API request/response logging
export LOG_API_CALLS=true
```

### 📊 Monitoring Setup

#### Prometheus Metrics
```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Key metrics to monitor:
# - api_requests_total
# - content_generation_duration_seconds
# - trend_collection_success_rate
# - database_connections_active
# - memory_usage_bytes
```

#### Grafana Dashboards
```bash
# Access Grafana
open http://localhost:3001

# Import dashboard templates
./scripts/import-grafana-dashboards.sh

# Set up alerts
./scripts/configure-alerts.sh
```

---

## 🚨 Emergency Procedures

### Production Outage Response

#### Immediate Actions (First 5 minutes)
1. **Acknowledge the Issue**
   ```bash
   # Check overall system status
   ./scripts/emergency-status.sh
   
   # Identify affected services
   kubectl get pods -n ai-content-factory-prod
   ```

2. **Notify Stakeholders**
   ```bash
   # Send status page update
   ./scripts/update-status-page.sh "investigating"
   
   # Alert team via Slack
   curl -X POST $SLACK_WEBHOOK -d '{"text":"🚨 Production issue detected"}'
   ```

3. **Quick Mitigation**
   ```bash
   # Scale up healthy services
   kubectl scale deployment content-engine --replicas=5
   
   # Route traffic away from failing services
   ./scripts/emergency-traffic-switch.sh
   ```

#### Investigation Phase (5-15 minutes)
```bash
# Collect emergency logs
./scripts/emergency-log-collection.sh

# Check recent deployments
kubectl rollout history deployment/content-engine

# Monitor key metrics
./scripts/emergency-metrics.sh

# Check external dependencies
./scripts/check-external-services.sh
```

#### Recovery Actions
```bash
# Rollback if needed
kubectl rollout undo deployment/content-engine

# Scale services
./scripts/emergency-scale.sh

# Restore from backup if needed
./scripts/emergency-restore.sh

# Clear caches
./scripts/emergency-cache-clear.sh
```

### Data Recovery Procedures

#### Database Recovery
```bash
# Check database integrity
./scripts/emergency-db-check.sh

# Restore from latest backup
./scripts/restore-database.sh latest

# Verify data consistency
./scripts/verify-data-integrity.sh

# Re-run failed migrations
./scripts/repair-migrations.sh
```

#### File Recovery
```bash
# Restore uploaded content
./scripts/restore-uploads.sh

# Verify file integrity
./scripts/verify-file-integrity.sh

# Regenerate missing thumbnails
./scripts/regenerate-thumbnails.sh
```

---

## 📚 Additional Resources

### Learning Resources
- **Architecture Deep Dive**: [architecture.md](architecture.md)
- **API Documentation**: [api/](api/)
- **Deployment Guides**: [deployment/](deployment/)
- **Video Tutorials**: https://youtube.com/ai-content-factory-tutorials

### Tools & Utilities
- **Log Analyzer**: `./scripts/analyze-logs.sh`
- **Performance Profiler**: `./scripts/profile-performance.sh`
- **Security Scanner**: `./scripts/security-scan.sh`
- **Backup Validator**: `./scripts/validate-backups.sh`

### External Dependencies Status
- **OpenAI Status**: https://status.openai.com
- **YouTube API Status**: https://developers.google.com/youtube/v3/status
- **Twitter API Status**: https://api.twitterstat.us
- **GitHub Status**: https://www.githubstatus.com

---

**Remember**: Most issues can be resolved by following the diagnostic steps systematically. When in doubt, start with the basics: check logs, verify configuration, and test connectivity. The AI Content Factory system is designed to be resilient and self-healing in many scenarios.

For urgent production issues, don't hesitate to use the emergency procedures and contact support immediately.

Stay calm, debug systematically, and document any fixes for future reference! 🔧✨