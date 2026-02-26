# Docker Deployment Guide

This guide shows how to deploy the Auto Assistent monorepo using Docker.

[🇷🇺 Русская версия](DOCKER.ru.md)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Copy `.env.example` to `.env` and fill in your credentials

## Quick Start

### 1. Prepare Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your credentials (use a text editor)
# Minimum required:
# - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
# - JWT_SECRET
# - ADMIN_PASSWORD
```

### 2. Build and Start All Services

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL database
- **Automatically run Alembic migrations** ✨
- **Automatically seed admin user** ✨
- Start Backend API (port 8000)
- Start Web Scraper (background worker)
- Start Telegram Bot (background worker)
- Start Frontend (port 5173)

### 3. Verify Services

```bash
# Check all services are running
docker-compose ps

# View backend logs (migrations + seeding)
docker-compose logs backend

# Should see:
#   ✅ PostgreSQL is ready!
#   🔄 Running Alembic migrations...
#   🌱 Seeding database...
#   🚀 Starting application...
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Login**: username `admin`, password from `.env` (default: `admin123`)

## No Manual Migration Needed! 🎉

The backend service now includes an **automatic init script** (`entrypoint.sh`) that:
1. ✅ Waits for PostgreSQL to be ready
2. ✅ Runs `alembic upgrade head` automatically
3. ✅ Seeds admin user (idempotent - won't duplicate)
4. ✅ Starts the application

You don't need to run migrations manually anymore!

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service (useful for debugging)
docker-compose logs -f backend
docker-compose logs -f scraper
docker-compose logs -f bot
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop all (containers remain)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes (⚠️ deletes database!)
docker-compose down -v
```

### Rebuild Images

```bash
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild and restart (forces new migration/seeding)
docker-compose up -d --build
```

### Manual Migration (if needed)

```bash
# Normally not needed - migrations run automatically
# But you can run them manually:
docker-compose exec backend alembic upgrade head

# Or create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Re-seed Database

```bash
# Seed script is idempotent - it won't duplicate admin user
docker-compose exec backend python seed.py
```

### Scale Services

```bash
# Run multiple scraper instances
docker-compose up -d --scale scraper=3
```

## Architecture

```
┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Nginx      │
│  (React)    │     │   :80        │
└─────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Backend    │
                    │   FastAPI    │
                    │   :8000      │
                    └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Scraper    │    │   Telegram   │    │  PostgreSQL  │
│   Worker     │    │     Bot      │    │     :5432    │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Image Sizes (Actual)

- **Backend**: 232 MB (multi-stage build)
- **Frontend**: 63 MB (Nginx + static files)
- **Bot**: 229 MB (includes OpenAI client)
- **Scraper**: 194 MB (httpx + BeautifulSoup4)
- **PostgreSQL**: 274 MB (Official `postgres:15-alpine`)

**Total: ~992 MB** (less than 1GB for entire stack)

## Security Features

✅ Multi-stage builds (small final images)
✅ Non-root users for all services
✅ Read-only volumes where possible
✅ Health checks for all services
✅ Isolated bridge network
✅ No build tools in production images
✅ Security headers in Nginx

## Production Considerations

### 1. Environment Variables

Update `.env` with production values:
- Use strong `JWT_SECRET` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Use strong database password
- Replace `localhost` in `DATABASE_URL` with service name `db`

### 2. SSL/HTTPS

Add a reverse proxy (e.g., Traefik, Nginx Proxy Manager) for SSL termination:

```yaml
# Example: Add to docker-compose.yml
  nginx-proxy:
    image: jwilder/nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs
```

### 3. Monitoring

Add monitoring services:

```yaml
  prometheus:
    image: prom/prometheus
    # ... configuration

  grafana:
    image: grafana/grafana
    # ... configuration
```

### 4. Backup Database

```bash
# Backup
docker-compose exec db pg_dump -U admin million_miles > backup.sql

# Restore
docker-compose exec -T db psql -U admin million_miles < backup.sql
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs backend

# Check health
docker-compose ps
```

### Database connection errors

```bash
# Ensure DB is healthy
docker-compose ps db

# Test connection
docker-compose exec backend python -c "from database import engine; print('OK')"
```

### Frontend can't reach backend

- Check `VITE_API_URL` in frontend environment
- Ensure backend is running: `curl http://localhost:8000/`

### Port already in use

```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # host:container
```

## Development vs Production

### Development (with hot reload)

```yaml
# Add to backend service
volumes:
  - ./backend:/app
command: uvicorn main:app --reload --host 0.0.0.0
```

### Production (optimized)

Use the provided Dockerfiles as-is for optimized production images.
