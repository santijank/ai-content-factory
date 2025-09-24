# Docker Setup Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Environment Setup](#docker-environment-setup)
- [Multi-Environment Configuration](#multi-environment-configuration)
- [Service Configuration](#service-configuration)
- [Networking & Storage](#networking--storage)
- [Production Deployment](#production-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

This guide covers deploying AI Content Factory using Docker and Docker Compose for development, staging, and production environments. Docker provides consistent, isolated environments with easy scaling and management capabilities.

### Why Docker?
- **Consistency**: Same environment across dev/staging/production
- **Isolation**: Services run in isolated containers
- **Scalability**: Easy horizontal scaling
- **Portability**: Runs anywhere Docker is supported
- **Efficiency**: Better resource utilization than VMs

## Prerequisites

### System Requirements

**Development Environment:**
- **CPU**: 4+ cores
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ free space
- **OS**: Ubuntu 20.04+, macOS 10.15+, Windows 10 Pro+

**Production Environment:**
- **CPU**: 16+ cores
- **RAM**: 32GB+ recommended
- **Storage**: 500GB+ SSD with backup
- **OS**: Ubuntu 20.04+ LTS (recommended)
- **Network**: Dedicated network interface

### Required Software

#### Docker Installation
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker run hello-world

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

#### macOS Installation
```bash
# Install via Homebrew
brew install --cask docker

# Or download Docker Desktop from:
# https://docs.docker.com/desktop/mac/install/
```

#### Windows Installation
```powershell
# Install Docker Desktop for Windows
# Download from: https://docs.docker.com/desktop/windows/install/

# Enable WSL 2 backend (recommended)
wsl --install
wsl --set-default-version 2
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ai-content-factory.git
cd ai-content-factory
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Applications
- **Main Dashboard**: http://localhost:5000
- **Web Dashboard**: http://localhost:3000
- **N8N Workflows**: http://localhost:5678
- **Monitoring**: http://localhost:9090

## Docker Environment Setup

### 📁 Project Structure
```
ai-content-factory/
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production overrides
├── docker-compose.override.yml     # Local overrides (optional)
├── .env                            # Environment variables
├── .env.example                    # Environment template
├── .dockerignore                   # Docker ignore patterns
├── trend-monitor/
│   ├── Dockerfile                  # Trend monitor image
│   └── requirements.txt
├── content-engine/
│   ├── Dockerfile                  # Content engine image
│   └── requirements.txt
├── platform-manager/
│   ├── Dockerfile                  # Platform manager image
│   └── requirements.txt
├── web-dashboard/
│   ├── Dockerfile                  # Frontend image
│   └── package.json
├── monitoring/
│   ├── Dockerfile                  # Monitoring stack
│   └── requirements.txt
└── data/                           # Persistent data
    ├── postgres/                   # Database data
    ├── redis/                      # Cache data
    ├── uploads/                    # File uploads
    └── logs/                       # Application logs
```

### 🐳 Main Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Database Services
  postgres:
    image: postgres:13-alpine
    container_name: ai-content-factory-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-content_factory}
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - ai-content-factory
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-admin} -d ${POSTGRES_DB:-content_factory}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ai-content-factory-redis
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD:-}
    volumes:
      - redis_data:/data
      - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - ai-content-factory
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf

  # Application Services
  trend-monitor:
    build:
      context: ./trend-monitor
      dockerfile: Dockerfile
    container_name: ai-content-factory-trend-monitor
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${POSTGRES_DB:-content_factory}
      - DB_USER=${POSTGRES_USER:-admin}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=redis://redis:6379
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - TWITTER_BEARER_TOKEN=${TWITTER_BEARER_TOKEN}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "8001:8001"
    networks:
      - ai-content-factory
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  content-engine:
    build:
      context: ./content-engine
      dockerfile: Dockerfile
    container_name: ai-content-factory-content-engine
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${POSTGRES_DB:-content_factory}
      - DB_USER=${POSTGRES_USER:-admin}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - QUALITY_TIER=${QUALITY_TIER:-budget}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./data/uploads:/app/uploads
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "8002:8002"
    networks:
      - ai-content-factory
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  platform-manager:
    build:
      context: ./platform-manager
      dockerfile: Dockerfile
    container_name: ai-content-factory-platform-manager
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${POSTGRES_DB:-content_factory}
      - DB_USER=${POSTGRES_USER:-admin}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./data/uploads:/app/uploads:ro
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "8003:8003"
    networks:
      - ai-content-factory
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Frontend
  web-dashboard:
    build:
      context: ./web-dashboard
      dockerfile: Dockerfile
      target: ${BUILD_TARGET:-development}
    container_name: ai-content-factory-web-dashboard
    environment:
      - REACT_APP_API_URL=http://localhost:5000
      - REACT_APP_WS_URL=ws://localhost:5000
      - NODE_ENV=${NODE_ENV:-development}
    volumes:
      - ./web-dashboard/src:/app/src:ro  # Development hot reload
      - ./web-dashboard/public:/app/public:ro
    ports:
      - "3000:3000"
    networks:
      - ai-content-factory
    depends_on:
      - main-app
    restart: unless-stopped

  # Main Application Gateway
  main-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-content-factory-main
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${POSTGRES_DB:-content_factory}
      - DB_USER=${POSTGRES_USER:-admin}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "5000:5000"
    networks:
      - ai-content-factory
    depends_on:
      trend-monitor:
        condition: service_healthy
      content-engine:
        condition: service_healthy
      platform-manager:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Workflow Orchestration
  n8n:
    image: n8nio/n8n:latest
    container_name: ai-content-factory-n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=${TZ:-UTC}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n-workflows:/home/node/.n8n/workflows:ro
    ports:
      - "5678:5678"
    networks:
      - ai-content-factory
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: ai-content-factory-prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - ai-content-factory
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: ai-content-factory-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3001:3000"
    networks:
      - ai-content-factory
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  n8n_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  ai-content-factory:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Multi-Environment Configuration

### 🔧 Environment Variables

#### Development (.env)
```bash
# Database Configuration
POSTGRES_DB=content_factory_dev
POSTGRES_USER=admin
POSTGRES_PASSWORD=dev_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=

# Application Settings
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# AI Service APIs
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
CLAUDE_API_KEY=your-claude-key
QUALITY_TIER=budget

# Platform APIs
YOUTUBE_API_KEY=your-youtube-key
TWITTER_BEARER_TOKEN=your-twitter-token

# N8N Configuration
N8N_PASSWORD=admin123
N8N_HOST=localhost

# Monitoring
GRAFANA_PASSWORD=admin

# Performance Settings
WORKER_PROCESSES=2
MAX_CONNECTIONS=100
```

#### Production (.env.prod)
```bash
# Database Configuration
POSTGRES_DB=content_factory_prod
POSTGRES_USER=app_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # Set in secrets
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# Application Settings
SECRET_KEY=${SECRET_KEY}  # Strong secret from secrets management
JWT_SECRET=${JWT_SECRET}
LOG_LEVEL=INFO
ENVIRONMENT=production

# AI Service APIs
OPENAI_API_KEY=${OPENAI_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
CLAUDE_API_KEY=${CLAUDE_API_KEY}
QUALITY_TIER=balanced

# Platform APIs
YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
TWITTER_BEARER_TOKEN=${TWITTER_BEARER_TOKEN}

# N8N Configuration
N8N_PASSWORD=${N8N_PASSWORD}
N8N_HOST=n8n.company.internal

# Monitoring
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Performance Settings
WORKER_PROCESSES=8
MAX_CONNECTIONS=1000

# Security
SSL_CERT_PATH=/certs/ssl.crt
SSL_KEY_PATH=/certs/ssl.key
```

### 📋 Production Overrides

#### docker-compose.prod.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./config/redis/redis-prod.conf:/usr/local/etc/redis/redis.conf
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  trend-monitor:
    environment:
      - WORKER_PROCESSES=4
      - LOG_LEVEL=INFO
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  content-engine:
    environment:
      - WORKER_PROCESSES=8
      - QUALITY_TIER=premium
      - LOG_LEVEL=INFO
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  platform-manager:
    environment:
      - WORKER_PROCESSES=4
      - LOG_LEVEL=INFO
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  web-dashboard:
    build:
      target: production
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Production Load Balancer
  nginx:
    image: nginx:alpine
    container_name: ai-content-factory-nginx
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - ai-content-factory
    depends_on:
      - main-app
      - web-dashboard
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'
```

## Service Configuration

### 🏗️ Individual Service Dockerfiles

#### Trend Monitor Dockerfile
```dockerfile
# trend-monitor/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start application
CMD ["python", "app.py"]
```

#### Content Engine Dockerfile
```dockerfile
# content-engine/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Start application
CMD ["python", "app.py"]
```

#### Web Dashboard Dockerfile
```dockerfile
# web-dashboard/Dockerfile
# Multi-stage build for production optimization
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy built assets
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Development stage
FROM node:18-alpine AS development

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]
```

### 🔧 Service Health Checks

#### Health Check Scripts
```bash
# scripts/health-check.sh
#!/bin/bash

echo "🔍 Checking AI Content Factory Health..."

# Check services
services=("postgres:5432" "redis:6379" "trend-monitor:8001" "content-engine:8002" "platform-manager:8003" "main-app:5000")

for service in "${services[@]}"; do
    host=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    if docker-compose exec $host nc -z localhost $port 2>/dev/null; then
        echo "✅ $host:$port is healthy"
    else
        echo "❌ $host:$port is not responding"
    fi
done

# Check HTTP endpoints
endpoints=("http://localhost:5000/health" "http://localhost:8001/health" "http://localhost:8002/health" "http://localhost:8003/health")

for endpoint in "${endpoints[@]}"; do
    if curl -sf $endpoint > /dev/null; then
        echo "✅ $endpoint is healthy"
    else
        echo "❌ $endpoint is not responding"
    fi
done
```

## Networking & Storage

### 🌐 Network Configuration

#### Custom Bridge Network
```yaml
# Advanced networking configuration
networks:
  ai-content-factory:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
    driver_opts:
      com.docker.network.bridge.name: ai-content-br
      com.docker.network.bridge.enable_ip_masquerade: 'true'
      com.docker.network.driver.mtu: 1500
```

#### Service Discovery
```yaml
# Internal service communication
services:
  trend-monitor:
    networks:
      ai-content-factory:
        aliases:
          - trend-monitor.internal
          - trends.internal
  
  content-engine:
    networks:
      ai-content-factory:
        aliases:
          - content-engine.internal
          - content.internal
```

### 💾 Volume Management

#### Named Volumes
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/ai-content-factory/data/postgres
      
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/ai-content-factory/data/redis
      
  uploads:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/ai-content-factory/data/uploads
```

#### Backup Volumes
```bash
# Create backup volume
docker volume create ai-content-factory-backup

# Backup database
docker run --rm \
  -v ai-content-factory_postgres_data:/data:ro \
  -v ai-content-factory-backup:/backup \
  alpine:latest \
  tar czf /backup/postgres-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Restore database
docker run --rm \
  -v ai-content-factory_postgres_data:/data \
  -v ai-content-factory-backup:/backup \
  alpine:latest \
  tar xzf /backup/postgres-20240915-030000.tar.gz -C /data
```

## Production Deployment

### 🚀 Production Setup

#### Pre-deployment Checklist
```bash
# 1. Server preparation
./scripts/prepare-production-server.sh

# 2. Security hardening
./scripts/harden-docker-security.sh

# 3. Configure secrets
./scripts/setup-secrets.sh

# 4. Setup monitoring
./scripts/setup-monitoring.sh

# 5. Configure backups
./scripts/setup-backups.sh
```

#### Production Environment
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
./scripts/verify-production-deployment.sh

# Monitor rollout
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 🔒 Security Configuration

#### Docker Security
```bash
# scripts/harden-docker-security.sh
#!/bin/bash

# Run containers as non-root
echo "Configuring non-root containers..."

# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Configure Docker daemon security
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp.json"
}
EOF

# Restart Docker
systemctl restart docker
```

#### Secrets Management
```yaml
# docker-compose.prod.yml with secrets
version: '3.8'

secrets:
  postgres_password:
    external: true
  redis_password:
    external: true
  openai_api_key:
    external: true

services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password
      
  content-engine:
    environment:
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key
    secrets:
      - openai_api_key
```

## Monitoring & Logging

### 📊 Container Monitoring

#### Resource Monitoring
```bash
# Monitor resource usage
docker stats

# Monitor specific service
docker stats ai-content-factory-content-engine

# Export metrics to Prometheus
docker run -d \
  --name docker-exporter \
  -p 9323:9323 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  prom/docker-exporter
```

#### Log Management
```yaml
# Centralized logging configuration
version: '3.8'

services:
  trend-monitor:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=trend-monitor"
        
  # ELK Stack for centralized logging
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./config/logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
      
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch
```

## Backup & Recovery

### 💾 Automated Backups

#### Backup Strategy
```bash
# scripts/backup-docker.sh
#!/bin/bash

BACKUP_DIR="/opt/backups/ai-content-factory"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup database
docker-compose exec -T postgres pg_dump -U admin content_factory | \
  gzip > $BACKUP_DIR/$DATE/database.sql.gz

# Backup volumes
docker run --rm \
  -v ai-content-factory_postgres_data:/data:ro \
  -v $BACKUP_DIR/$DATE:/backup \
  alpine:latest \
  tar czf /backup/postgres_data.tar.gz -C /data .

docker run --rm \
  -v ai-content-factory_uploads:/data:ro \
  -v $BACKUP_DIR/$DATE:/backup \
  alpine:latest \
  tar czf /backup/uploads.tar.gz -C /data .

# Backup configuration
tar czf $BACKUP_DIR/$DATE/config.tar.gz config/ .env docker-compose*.yml

# Clean old backups (keep 30 days)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

#### Recovery Procedures
```bash
# scripts/restore-docker.sh
#!/bin/bash

BACKUP_DATE=${1:-latest}
BACKUP_DIR="/opt/backups/ai-content-factory"

if [ "$BACKUP_DATE" = "latest" ]; then
    BACKUP_PATH=$(ls -1d $BACKUP_DIR/* | tail -1)
else
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_DATE"
fi

echo "Restoring from: $BACKUP_PATH"

# Stop services
docker-compose down

# Restore database
docker-compose up -d postgres
sleep 10
gunzip -c $BACKUP_PATH/database.sql.gz | \
  docker-compose exec -T postgres psql -U admin content_factory

# Restore volumes
docker run --rm \
  -v ai-content-factory_postgres_data:/data \
  -v $BACKUP_PATH:/backup:ro \
  alpine:latest \
  tar xzf /backup/postgres_data.tar.gz -C /data

# Restore configuration
tar xzf $BACKUP_PATH/config.tar.gz

# Start all services
docker-compose up -d

echo "Restore completed from: $BACKUP_PATH"
```

## Performance Optimization

### ⚡ Container Optimization

#### Resource Limits
```yaml
# Optimized resource allocation
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    environment:
      # PostgreSQL optimization
      POSTGRES_SHARED_BUFFERS: 512MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
      POSTGRES_WORK_MEM: 4MB
      POSTGRES_MAINTENANCE_WORK_MEM: 64MB

  redis:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    environment:
      # Redis optimization
      REDIS_MAXMEMORY: 768mb
      REDIS_MAXMEMORY_POLICY: allkeys-lru

  content-engine:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    environment:
      # Application optimization
      WORKER_PROCESSES: 4
      MAX_CONCURRENT_JOBS: 3
      CACHE_SIZE: 512MB
```

#### Docker Performance Tuning
```bash
# Docker daemon optimization
cat > /etc/docker/daemon.json << EOF
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "default-ulimits": {
    "nofile": {
      "name": "nofile",
      "hard": 64000,
      "soft": 64000
    }
  }
}
EOF

# Restart Docker
systemctl restart docker
```

### 📈 Scaling Configuration

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  content-engine:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  trend-monitor:
    deploy:
      replicas: 2
      
  platform-manager:
    deploy:
      replicas: 2

  # Load balancer for scaled services
  nginx:
    image: nginx:alpine
    volumes:
      - ./config/nginx/load-balancer.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - content-engine
      - trend-monitor
      - platform-manager
```

#### Auto-scaling with Docker Swarm
```bash
# Initialize Docker Swarm
docker swarm init

# Deploy stack with auto-scaling
docker stack deploy -c docker-compose.yml -c docker-compose.scale.yml ai-content-factory

# Scale services manually
docker service scale ai-content-factory_content-engine=5

# Monitor scaling
docker service ls
```

## Troubleshooting

### 🔍 Common Issues

#### Container Startup Issues
```bash
# Check container logs
docker-compose logs [service-name]

# Check container status
docker-compose ps

# Inspect container configuration
docker inspect ai-content-factory-content-engine

# Check resource usage
docker stats ai-content-factory-content-engine

# Debug container interactively
docker-compose exec content-engine bash
```

#### Network Issues
```bash
# Check network connectivity
docker network ls
docker network inspect ai-content-factory_ai-content-factory

# Test inter-service communication
docker-compose exec content-engine ping postgres
docker-compose exec content-engine nc -zv postgres 5432

# Check port mappings
docker-compose port postgres 5432
```

#### Volume Issues
```bash
# Check volume mounts
docker volume ls
docker volume inspect ai-content-factory_postgres_data

# Check file permissions
docker-compose exec postgres ls -la /var/lib/postgresql/data
docker-compose exec content-engine ls -la /app/uploads

# Fix permission issues
docker-compose exec postgres chown -R postgres:postgres /var/lib/postgresql/data
```

### 🛠️ Debug Tools

#### Container Debugging
```bash
# scripts/debug-container.sh
#!/bin/bash

SERVICE=${1:-content-engine}

echo "🔍 Debugging $SERVICE..."

# Basic information
echo "Container Status:"
docker-compose ps $SERVICE

echo "Resource Usage:"
docker stats --no-stream $SERVICE

echo "Recent Logs:"
docker-compose logs --tail=50 $SERVICE

echo "Container Processes:"
docker-compose exec $SERVICE ps aux

echo "Network Configuration:"
docker-compose exec $SERVICE cat /etc/hosts
docker-compose exec $SERVICE ip route

echo "Environment Variables:"
docker-compose exec $SERVICE env | grep -E "(DB_|REDIS_|API_)"

echo "File System:"
docker-compose exec $SERVICE df -h
```

#### Performance Analysis
```bash
# scripts/performance-analysis.sh
#!/bin/bash

echo "📊 Performance Analysis..."

# Container resource usage
echo "=== Resource Usage ==="
docker stats --no-stream

# Database performance
echo "=== Database Performance ==="
docker-compose exec postgres psql -U admin -d content_factory -c "
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  min_time,
  max_time
FROM pg_stat_statements 
WHERE calls > 100 
ORDER BY mean_time DESC 
LIMIT 10;"

# Redis performance
echo "=== Redis Performance ==="
docker-compose exec redis redis-cli info stats

# Application metrics
echo "=== Application Metrics ==="
curl -s http://localhost:5000/metrics | grep -E "(response_time|request_count|error_rate)"
```

### 🚨 Emergency Procedures

#### Quick Recovery
```bash
# scripts/emergency-recovery.sh
#!/bin/bash

echo "🚨 Emergency Recovery Procedure"

# Stop all services
echo "Stopping services..."
docker-compose down

# Clean up problematic containers
echo "Cleaning up containers..."
docker container prune -f

# Clean up networks
echo "Cleaning up networks..."
docker network prune -f

# Check disk space
echo "Checking disk space..."
df -h

# Restart services
echo "Restarting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 30

# Health check
echo "Running health check..."
./scripts/health-check.sh

echo "Emergency recovery completed!"
```

#### Rollback Deployment
```bash
# scripts/rollback-deployment.sh
#!/bin/bash

PREVIOUS_VERSION=${1:-previous}

echo "🔄 Rolling back to $PREVIOUS_VERSION..."

# Stop current deployment
docker-compose down

# Switch to previous version
git checkout $PREVIOUS_VERSION

# Restore previous configuration
if [ -f ".env.$PREVIOUS_VERSION" ]; then
    cp .env.$PREVIOUS_VERSION .env
fi

# Deploy previous version
docker-compose pull
docker-compose up -d

# Verify rollback
./scripts/health-check.sh

echo "Rollback completed!"
```

---

## 📚 Quick Reference

### Essential Commands
```bash
# Service Management
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose restart [service]  # Restart specific service
docker-compose scale content-engine=3  # Scale service

# Monitoring
docker-compose ps                 # Service status
docker-compose logs -f [service]  # Follow logs
docker stats                      # Resource usage
docker system df                  # Disk usage

# Maintenance
docker system prune -a            # Clean up everything
docker volume prune               # Clean up volumes
docker network prune              # Clean up networks
docker image prune -a             # Clean up images

# Backup & Restore
./scripts/backup-docker.sh        # Create backup
./scripts/restore-docker.sh DATE  # Restore from backup
```

### Port Mappings
| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| Main App | 5000 | 5000 | Main application |
| Web Dashboard | 3000 | 3000 | React frontend |
| Trend Monitor | 8001 | 8001 | Trend collection API |
| Content Engine | 8002 | 8002 | Content generation API |
| Platform Manager | 8003 | 8003 | Upload management API |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |
| N8N | 5678 | 5678 | Workflow automation |
| Prometheus | 9090 | 9090 | Metrics collection |
| Grafana | 3000 | 3001 | Monitoring dashboard |

### Environment Files
- `.env` - Main environment configuration
- `.env.example` - Template with default values
- `.env.prod` - Production-specific settings
- `.env.local` - Local development overrides

---

**Remember**: Docker provides consistent, portable deployments but requires proper resource management and monitoring. Always test configuration changes in development before applying to production.

For Kubernetes deployment, see [kubernetes-setup.md](kubernetes-setup.md). For local development without Docker, see [local-setup.md](local-setup.md).

Happy containerizing! 🐳🚀