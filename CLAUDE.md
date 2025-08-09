# Claude Context - Automation Platform

## Project Overview

This is a Docker-based automation platform designed for marketing content generation and ad campaign management. The system follows a GitOps approach where the Git repository is the single source of truth, and the production server only runs containers.

## Architecture Philosophy

- **Separation of Concerns**: The droplet/server is "runtime only" - no direct code editing on production
- **GitOps Workflow**: All changes go through Git (commit → push → pull → deploy)
- **Container-First**: Everything runs in Docker containers for consistency and isolation
- **Security-First**: Secrets stay out of Git, use environment variables, implement proper authentication

## System Components

### Core Services
1. **Caddy** (Reverse Proxy)
   - Handles TLS certificates automatically via Let's Encrypt
   - Routes traffic to appropriate services based on domain
   - Provides compression (zstd, gzip)

2. **n8n** (Workflow Automation)
   - Visual workflow builder for automation
   - Persistent storage in PostgreSQL
   - Protected with basic authentication
   - Handles orchestration of content generation and publishing

3. **PostgreSQL** (Database)
   - Dedicated database for n8n workflows
   - Persistent volume storage
   - Version 15 for stability

4. **Content API** (FastAPI Service)
   - Python-based microservice
   - Handles content generation via LLM integration
   - Manages ad publishing to various platforms
   - Stateless design for scalability

## Development Guidelines

### When Making Changes

1. **Never modify production directly** - Always work locally, test, commit, and deploy
2. **Check existing patterns** - Before adding new functionality, examine how similar features are implemented
3. **Maintain consistency** - Follow the established code style and structure
4. **Document API changes** - Update endpoints and payload examples in comments or docs

### Security Considerations

- **Never commit secrets** - Use `.env` files and environment variables
- **Validate all inputs** - Especially in the FastAPI service
- **Use strong passwords** - For n8n basic auth and database
- **Implement rate limiting** - For public-facing endpoints (future enhancement)
- **Regular updates** - Keep Docker images updated for security patches

### File Structure Rules

```
playground-automation/
├── infra/                    # Infrastructure configuration
│   ├── docker-compose.yml    # Service orchestration
│   ├── Caddyfile            # Reverse proxy rules
│   └── .env                 # LOCAL ONLY - never commit
├── services/                 # Microservices
│   └── content-api/         # Each service in its own directory
│       ├── app/             # Application code
│       ├── requirements.txt # Python dependencies
│       └── Dockerfile       # Container definition
└── scripts/                 # Deployment and utility scripts (if needed)
```

## API Design Principles

### Content API Endpoints

- **RESTful design** - Use proper HTTP verbs (GET, POST, PUT, DELETE)
- **Consistent responses** - Always return JSON with status indicators
- **Error handling** - Return meaningful error messages with appropriate HTTP codes
- **Versioning ready** - Structure allows for `/v1/`, `/v2/` prefixes if needed

### Current Endpoints

- `GET /health` - Service health check (no auth required)
- `POST /generate-campaign` - Generate marketing content (requires API key via n8n)
- `POST /ads/publish` - Queue ad for publishing (requires API key via n8n)

## n8n Workflow Patterns

### Standard Workflow Structure
1. **Trigger** (Cron, Webhook, or Manual)
2. **Data Preparation** (Set variables, format inputs)
3. **API Call** (to Content API or external services)
4. **Human Review** (optional approval step via webhook)
5. **Publishing** (to social platforms or ad networks)
6. **Logging** (track success/failure)

### Integration Points
- Content API for generation tasks
- Platform APIs (Meta, Google, LinkedIn) for publishing
- Webhook nodes for human-in-the-loop approval
- Database nodes for analytics storage

## Deployment Process

### Standard Deployment
```bash
# Local development
git add .
git commit -m "feat: describe change"
git push origin main

# On production server
cd /path/to/repo
git pull
cd infra
docker compose up -d --build
```

### Environment Variables

Required in `infra/.env`:
- `N8N_HOST` - n8n subdomain
- `API_HOST` - API subdomain  
- `N8N_DB_*` - PostgreSQL credentials
- `N8N_BASIC_*` - n8n authentication
- `OPENAI_API_KEY` - For content generation
- `META_ACCESS_TOKEN` - For Meta/Facebook integration

## Future Enhancements Priority

1. **Immediate**
   - Implement actual LLM integration (replace stub in Content API)
   - Add proper Meta/Google Ads API integration
   - Set up basic monitoring (health checks)

2. **Short-term**
   - GitHub Actions for CI/CD
   - Structured logging with log aggregation
   - Rate limiting on public endpoints
   - Input validation improvements

3. **Long-term**
   - Horizontal scaling for Content API
   - Message queue for async processing
   - Advanced analytics dashboard
   - Multi-tenant support

## Troubleshooting Guide

### Common Issues

1. **Service won't start**
   - Check Docker logs: `docker compose logs [service-name]`
   - Verify environment variables are set
   - Ensure ports aren't already in use

2. **TLS certificate issues**
   - Verify DNS is properly configured
   - Check Caddy has write permissions to volumes
   - Ensure ports 80/443 are open in firewall

3. **n8n can't connect to API**
   - Verify both services are on same Docker network
   - Check service names match in docker-compose.yml
   - Test with internal Docker DNS (e.g., `content-api:8000`)

4. **Database connection failures**
   - Confirm PostgreSQL is running
   - Verify credentials match in .env
   - Check Docker network connectivity

## Testing Approach

### Local Testing
```bash
# Start services locally
cd infra
docker compose up

# Test API endpoints
curl http://localhost:8000/health
```

### Integration Testing
- Use n8n's built-in testing for workflows
- Test API endpoints with Postman/Insomnia
- Verify service communication within Docker network

## Performance Considerations

- **Content API**: Stateless design allows horizontal scaling
- **n8n**: Single instance sufficient for most workloads
- **PostgreSQL**: Monitor size, implement cleanup policies for old workflow data
- **Caddy**: Minimal overhead, handles thousands of requests efficiently

## Backup Strategy

### Critical Data
1. **n8n workflows** - Stored in PostgreSQL and n8n_data volume
2. **Environment config** - Keep secure backup of .env file
3. **Custom code** - All in Git repository

### Backup Commands
```bash
# Backup n8n data volume
docker run --rm -v playground-automation_n8n_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/n8n-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup PostgreSQL
docker compose exec postgres pg_dump -U ${N8N_DB_USER} ${N8N_DB_NAME} \
  > backups/db-backup-$(date +%Y%m%d).sql
```

## Monitoring Checklist

- [ ] All services running: `docker compose ps`
- [ ] API responding: `curl https://api.yourdomain.com/health`
- [ ] n8n accessible: Check `https://n8n.yourdomain.com`
- [ ] TLS certificates valid: Check browser padlock
- [ ] Disk space adequate: `df -h`
- [ ] Memory usage normal: `docker stats`

## Contact & Support

For issues or questions:
1. Check logs first: `docker compose logs -f [service]`
2. Review this documentation
3. Check n8n community forums for workflow issues
4. Review FastAPI/Pydantic docs for API issues

## Important Notes for Development

- **Always test locally first** using `docker compose up`
- **Use meaningful commit messages** following conventional commits
- **Document any new environment variables** in .env.example
- **Update this file** when architecture changes significantly
- **Consider backwards compatibility** when modifying APIs
- **Plan for failure** - implement proper error handling and retries