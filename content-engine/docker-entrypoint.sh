#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting AI Content Factory - Content Engine${NC}"

# Function to check if database is ready
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database connection...${NC}"
    
    while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'content_factory'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    conn.close()
    print('Database is ready!')
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
" 2>/dev/null; do
        echo -e "${YELLOW}⏳ Database is not ready yet. Retrying in 5 seconds...${NC}"
        sleep 5
    done
    
    echo -e "${GREEN}✅ Database connection established!${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}🔄 Running database migrations...${NC}"
    
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        echo -e "${GREEN}✅ Migrations completed!${NC}"
    else
        echo -e "${YELLOW}⚠️  No alembic.ini found, skipping migrations${NC}"
    fi
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
    
    mkdir -p /app/logs
    mkdir -p /app/uploads
    mkdir -p /app/temp
    mkdir -p /app/generated_content
    mkdir -p /app/cache
    
    echo -e "${GREEN}✅ Directories created!${NC}"
}

# Function to validate environment variables
validate_environment() {
    echo -e "${YELLOW}🔍 Validating environment variables...${NC}"
    
    required_vars=("DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=($var)
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing required environment variables: ${missing_vars[*]}${NC}"
        echo -e "${YELLOW}💡 Please check your .env file or environment configuration${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Environment validation passed!${NC}"
}

# Function to check AI service configurations
check_ai_services() {
    echo -e "${YELLOW}🤖 Checking AI service configurations...${NC}"
    
    # Check if at least one AI service is configured
    ai_services_configured=false
    
    if [ ! -z "$GROQ_API_KEY" ]; then
        echo -e "${GREEN}✅ Groq API configured${NC}"
        ai_services_configured=true
    fi
    
    if [ ! -z "$OPENAI_API_KEY" ]; then
        echo -e "${GREEN}✅ OpenAI API configured${NC}"
        ai_services_configured=true
    fi
    
    if [ ! -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${GREEN}✅ Anthropic Claude API configured${NC}"
        ai_services_configured=true
    fi
    
    if [ "$ai_services_configured" = false ]; then
        echo -e "${YELLOW}⚠️  No AI services configured. Content generation will use fallback methods.${NC}"
    fi
}

# Function to start the application
start_application() {
    echo -e "${BLUE}🎬 Starting Content Engine Service...${NC}"
    
    # Determine startup mode based on environment
    if [ "$APP_ENV" = "development" ]; then
        echo -e "${YELLOW}🔧 Starting in development mode${NC}"
        exec python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload
    elif [ "$APP_ENV" = "production" ]; then
        echo -e "${GREEN}🚀 Starting in production mode${NC}"
        exec gunicorn --bind 0.0.0.0:8002 \
                     --workers 4 \
                     --worker-class uvicorn.workers.UvicornWorker \
                     --worker-connections 1000 \
                     --max-requests 1000 \
                     --max-requests-jitter 100 \
                     --timeout 300 \
                     --keep-alive 5 \
                     --access-logfile - \
                     --error-logfile - \
                     --log-level info \
                     app:app
    else
        echo -e "${YELLOW}🔧 Starting in default mode${NC}"
        exec python -m uvicorn app:app --host 0.0.0.0 --port 8002
    fi
}

# Main execution flow
main() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  AI Content Factory