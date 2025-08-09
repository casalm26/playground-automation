# 🚀 Content Automation Platform

A comprehensive Docker-based marketing automation platform with AI-powered content generation, multi-platform publishing, and analytics. Built with n8n orchestration, FastAPI microservices, and enterprise-grade monitoring.

## ✨ Features

### 🤖 AI-Powered Content Generation
- Multi-platform content creation (LinkedIn, Facebook, Instagram, Twitter, Blog, Email)
- OpenAI integration with customizable prompts
- A/B testing variations
- SEO-optimized blog posts
- Email campaign generation with personalization

### 🔄 Workflow Automation
- Visual n8n workflows for content pipelines
- Human-in-the-loop approval processes
- Scheduled content generation
- Multi-platform publishing
- Error handling and retry logic

### 📊 Analytics & Monitoring
- Real-time performance metrics
- Platform-specific analytics collection
- Comprehensive health monitoring
- Prometheus metrics export
- Custom dashboards and reports

### 🔒 Enterprise Security
- API key authentication
- Rate limiting
- HTTPS with automatic TLS certificates
- Database encryption
- Audit logging

## 🏗️ Architecture

- **Caddy**: Reverse proxy with automatic TLS certificates
- **n8n**: Visual workflow automation platform
- **PostgreSQL**: Dual databases (n8n workflows + application data)
- **Redis**: Queuing and caching
- **FastAPI**: High-performance content generation API
- **Docker**: Containerized deployment

## Project Structure

```
.
├── infra/
│   ├── docker-compose.yml     # Main orchestration
│   ├── Caddyfile              # Reverse proxy config
│   └── .env.example           # Environment template
├── services/
│   └── content-api/           # FastAPI service
│       ├── app/
│       │   └── main.py
│       ├── requirements.txt
│       └── Dockerfile
└── .gitignore
```

## 🚀 Quick Start

### Automated Deployment

Use the deployment script for a guided setup:

```bash
# Clone the repository
git clone <your-repo-url>
cd playground-automation

# Run automated deployment
./scripts/deploy.sh
```

The script will:
- Validate system requirements
- Check Docker installation
- Configure environment variables
- Deploy all services
- Run health checks
- Provide access information

### Manual Setup

If you prefer manual setup:

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose v2
- Domain with DNS control
- 4GB+ RAM recommended
- 20GB+ disk space

## 🛠️ Initial Setup

### 1. DNS Configuration

Create A records pointing to your server:
- `n8n.yourdomain.com` → Server IP
- `api.yourdomain.com` → Server IP

### 2. Server Setup

Install Docker on Ubuntu:

```bash
sudo apt update && sudo apt -y install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and back in to apply docker group permissions.

### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/you/your-repo.git
cd your-repo/infra

# Configure environment
cp .env.example .env
# Edit .env with your actual values

# Start services
docker compose up -d --build
```

## Environment Variables

Copy `infra/.env.example` to `infra/.env` and configure:

- `N8N_HOST`: n8n subdomain (e.g., n8n.yourdomain.com)
- `API_HOST`: API subdomain (e.g., api.yourdomain.com)
- `N8N_DB_USER/PASS/NAME`: PostgreSQL credentials
- `N8N_BASIC_USER/PASS`: n8n UI authentication
- `OPENAI_API_KEY`: OpenAI API key for content generation
- `META_ACCESS_TOKEN`: Meta/Facebook API token

## 🌐 Services

### Content API (`https://api.yourdomain.com`)
**AI-powered content generation and automation API**

#### Core Endpoints:
- `GET /health` - Comprehensive health check with system metrics
- `GET /metrics` - Prometheus-compatible metrics
- `POST /generate-campaign` - Multi-platform content generation
- `POST /generate-blog` - SEO-optimized blog posts
- `POST /generate-email` - Email campaigns with personalization
- `POST /ads/publish` - Ad publishing to platforms
- `POST /webhook/n8n` - n8n workflow callbacks
- `POST /schedule/content` - Content scheduling
- `GET /analytics/report/{campaign_id}` - Performance analytics

#### Platform Integrations:
- **OpenAI**: GPT-4 powered content generation
- **Meta Graph API**: Facebook & Instagram publishing
- **LinkedIn API**: Professional content distribution
- **Twitter API**: Tweet automation
- **Google Ads API**: Advertising campaign management

### n8n Workflow Platform (`https://n8n.yourdomain.com`)
**Visual workflow automation interface**

- Protected with basic authentication
- Persistent workflows stored in PostgreSQL
- Pre-built templates for common automation
- Human-in-the-loop approval processes
- Error handling and retry mechanisms

## n8n Workflow Examples

### Basic Content Generation Workflow

1. **Trigger**: Cron schedule or webhook
2. **HTTP Request**: POST to `https://api.yourdomain.com/generate-campaign`
   ```json
   {
     "product": "Your Product",
     "persona": "Target Audience",
     "tone": "professional"
   }
   ```
3. **Process Output**: Use generated content for social posts
4. **Human Approval**: Add webhook node for approval flow
5. **Publish**: Call platform APIs or `/ads/publish` endpoint

## Updates and Deployment

```bash
# On local machine
git add .
git commit -m "Update message"
git push origin main

# On server
cd your-repo
git pull
cd infra
docker compose up -d --build
```

## Monitoring

View logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f content-api
```

Check service status:
```bash
docker compose ps
```

## Backup

n8n workflows and data are persisted in Docker volumes. To backup:

```bash
# Backup n8n data
docker run --rm -v playground-automation_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n-backup.tar.gz -C /data .

# Backup PostgreSQL
docker compose exec postgres pg_dump -U $N8N_DB_USER $N8N_DB_NAME > n8n-db-backup.sql
```

## Troubleshooting

### Service not accessible
- Check DNS propagation: `dig n8n.yourdomain.com`
- Verify firewall allows ports 80 and 443
- Check Caddy logs: `docker compose logs caddy`

### n8n database connection issues
- Verify PostgreSQL is running: `docker compose ps postgres`
- Check credentials in `.env` file
- Review n8n logs: `docker compose logs n8n`

### FastAPI errors
- Check API logs: `docker compose logs content-api`
- Verify environment variables are set
- Test locally: `curl https://api.yourdomain.com/health`

## Security Notes

- Never commit `.env` file (included in .gitignore)
- Use strong passwords for n8n basic auth
- Keep API keys secure and rotate regularly
- Consider implementing rate limiting for public endpoints
- Enable firewall on server (allow only 22, 80, 443)

## Next Steps

1. Implement actual LLM integration in FastAPI service
2. Add Meta/Google Ads API integration
3. Set up CI/CD with GitHub Actions
4. Add monitoring (Prometheus/Grafana)
5. Implement proper logging aggregation
6. Add data persistence backup strategy