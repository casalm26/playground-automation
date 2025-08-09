#!/bin/bash

# Deployment script for Content Automation Platform
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
echo "🚀 Deploying Content Automation Platform - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Do not run this script as root${NC}"
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

# Navigate to project directory
cd "$(dirname "$0")/.."

# Check if .env file exists
if [ ! -f "infra/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example${NC}"
    cp infra/.env.example infra/.env
    echo -e "${RED}❗ Please edit infra/.env with your actual configuration before continuing${NC}"
    echo "Required variables:"
    echo "  - N8N_HOST (your n8n domain)"
    echo "  - API_HOST (your api domain)"
    echo "  - API_KEY (secure API key)"
    echo "  - OPENAI_API_KEY (OpenAI API key)"
    echo "  - Database passwords"
    echo "  - Platform API tokens"
    read -p "Press enter after configuring .env file..."
fi

# Validate required environment variables
echo "🔍 Validating environment configuration..."
source infra/.env

required_vars=("N8N_HOST" "API_HOST" "API_KEY" "N8N_DB_USER" "N8N_DB_PASS" "APP_DB_USER" "APP_DB_PASS")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configuration is valid${NC}"

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check disk space (need at least 2GB free)
available_space=$(df / | awk 'NR==2 {print $4}')
if [ "$available_space" -lt 2097152 ]; then # 2GB in KB
    echo -e "${YELLOW}⚠️  Low disk space. Available: $(($available_space / 1024))MB${NC}"
fi

# Check if ports are available
check_port() {
    if ss -tuln | grep -q ":$1 "; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

if ! check_port 80 || ! check_port 443; then
    echo -e "${RED}❌ Required ports (80, 443) are not available${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-deployment checks passed${NC}"

# Pull latest changes (if in a git repository)
if [ -d ".git" ]; then
    echo "📦 Pulling latest changes..."
    git pull origin main || true
fi

# Navigate to infra directory
cd infra

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down || true

# Remove old images (optional, saves space)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🧹 Cleaning up old Docker images..."
    docker image prune -f || true
fi

# Build and start services
echo "🔨 Building and starting services..."
docker compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Running health checks..."
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null; then
            echo -e "${GREEN}✅ $service is healthy${NC}"
            return 0
        fi
        echo "⏳ Waiting for $service (attempt $attempt/$max_attempts)..."
        sleep 10
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $service failed health check${NC}"
    return 1
}

# Check if services are responding
if ! check_service "Content API" "http://localhost:8000/health/simple"; then
    echo -e "${RED}❌ Content API is not responding${NC}"
    docker compose logs content-api
    exit 1
fi

# Check if n8n is accessible (if N8N_HOST is localhost or IP)
if [[ "$N8N_HOST" == "localhost"* ]] || [[ "$N8N_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    if ! check_service "n8n" "http://$N8N_HOST"; then
        echo -e "${YELLOW}⚠️  n8n might not be ready yet, but this is normal for first startup${NC}"
    fi
fi

# Check database connectivity
echo "🗄️  Checking database connectivity..."
if docker compose exec -T postgres-app pg_isready -U "$APP_DB_USER" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application database is ready${NC}"
else
    echo -e "${RED}❌ Application database is not ready${NC}"
    docker compose logs postgres-app
    exit 1
fi

# Show service status
echo "📊 Service Status:"
docker compose ps

# Show resource usage
echo "💻 Resource Usage:"
docker compose top

# Display access information
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "📱 Access Information:"
echo "  Content API: https://$API_HOST"
echo "  API Docs: https://$API_HOST/docs"
echo "  Health Check: https://$API_HOST/health"
echo "  Metrics: https://$API_HOST/metrics"
echo ""
echo "  n8n Interface: https://$N8N_HOST"
echo "  n8n Credentials: $N8N_BASIC_USER / [password in .env]"
echo ""
echo "🔧 Management Commands:"
echo "  View logs: docker compose logs -f [service]"
echo "  Restart services: docker compose restart"
echo "  Stop all: docker compose down"
echo "  Update: git pull && docker compose up -d --build"
echo ""

# Show next steps
echo "🚀 Next Steps:"
echo "1. Test the API endpoints"
echo "2. Import n8n workflow templates from n8n-workflows/"
echo "3. Configure platform integrations (LinkedIn, Meta, etc.)"
echo "4. Set up monitoring and alerts"
echo "5. Create your first content campaign"
echo ""

# Offer to run a basic test
read -p "Would you like to run a basic API test? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Testing API..."
    
    # Test health endpoint
    if response=$(curl -s "http://localhost:8000/health/simple"); then
        echo -e "${GREEN}✅ API Health Check: $response${NC}"
    else
        echo -e "${RED}❌ API Health Check failed${NC}"
    fi
    
    # Test with API key (if not using default)
    if [ "$API_KEY" != "your-secure-api-key-here" ]; then
        echo "🔑 Testing authenticated endpoint..."
        if response=$(curl -s -H "X-API-Key: $API_KEY" "http://localhost:8000/"); then
            echo -e "${GREEN}✅ Authenticated request: $(echo $response | jq -r '.name // .')"
        else
            echo -e "${RED}❌ Authenticated request failed${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✨ Deployment complete! Your Content Automation Platform is ready.${NC}"

# Log deployment
echo "$(date): Deployment completed successfully" >> deployment.log