# 🚗 Auto Assistent - Car Inventory Management System

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready, full-stack car inventory management system with automated web scraping, intelligent search capabilities, and a responsive admin dashboard.

[🇷🇺 Русская версия](README.ru.md)

---

## 📋 Project Overview

**Auto Assistent** is a comprehensive car inventory management platform that automates the collection, storage, and presentation of car listings from Japanese automotive marketplaces. The system follows a modern microservices architecture:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Scraper   │────▶│  PostgreSQL  │◀────│   Backend    │
│ (Worker)    │     │   Database   │     │   (FastAPI)  │
└─────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  Telegram    │     │   Frontend   │
                    │     Bot      │     │   (React)    │
                    └──────────────┘     └──────────────┘
```

### Data Flow

1. **Scraper** extracts car listings from carsensor.net and stores them in PostgreSQL
2. **Backend API** provides RESTful endpoints with JWT authentication
3. **Frontend Dashboard** displays listings with infinite scroll and server-side search
4. **Telegram Bot** enables natural language queries powered by OpenAI GPT

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ ([Install](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ ([Install](https://docs.docker.com/compose/install/))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/auto-assistent-llm.git
cd auto-assistent-llm

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your credentials:
#   - Set POSTGRES_PASSWORD (strong password)
#   - Set JWT_SECRET (generate: python -c "import secrets; print(secrets.token_urlsafe(32))")
#   - Set TG_BOT_TOKEN (from @BotFather - see section below)
#   - Set AI_API_KEY (from OpenAI)

# 3. Start all services (migrations & seeding run automatically)
docker-compose up -d

# 4. Verify services are running
docker-compose ps
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:5173 | `admin` / `admin123` |
| **Backend API** | http://localhost:8000 | JWT required |
| **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| **Telegram Bot** | Your bot username | Natural language queries |

### Default Admin Credentials

```
Username: admin
Password: admin123 (change in .env before deployment)
```

### Setup Telegram Bot (Optional)

If you want to use the Telegram bot feature, you need to create a bot with BotFather:

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send the command `/newbot`
3. Follow the prompts:
   - Enter a **name** for your bot (e.g., "Auto Assistent")
   - Enter a **username** for your bot (must end with "bot", e.g., "auto_assistent_llm_bot")
4. BotFather will respond with your bot token. It looks like this:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```
5. Copy this token and paste it into the `TG_BOT_TOKEN` variable in your `.env` file
6. (Optional) Customize your bot:
   - `/setdescription` - Set bot description
   - `/setabouttext` - Set "About" text
   - `/setuserpic` - Set bot profile picture

**Note:** Keep your bot token secure and never commit it to version control!

---

## 🎯 Architectural Decisions

### 1. Scraping Strategy: httpx + BeautifulSoup

We use `httpx` with `BeautifulSoup4` instead of browser automation (Playwright/Selenium) because:
- **carsensor.net serves static HTML** - no JavaScript rendering needed
- **10x lower resource usage** - ~50MB RAM vs ~500MB for browser instances
- **Faster execution** - 50-200ms per request vs 2-5 seconds with browser startup
- **Smaller Docker images** - ~150MB vs ~1.5GB with Chromium
- **Simpler scaling** - stateless workers are easier to horizontally scale

### 2. Cursor-Based Pagination

We use cursor-based pagination (`WHERE id < cursor`) instead of offset/limit because:
- **Constant performance** - O(1) index seeks regardless of page depth
- **No data skipping** - cursor maintains position when new items are inserted
- **No duplicates** - prevents showing same item twice during concurrent operations
- **Better for infinite scroll** - predictable low latency on large datasets

### 3. Frontend Stack: Ant Design + TanStack Query

**Ant Design** provides:
- Professional enterprise UI components out of the box
- Built-in responsive patterns (Table for desktop, List for mobile)
- 100+ ready-to-use components accelerating development

**TanStack Query** handles:
- Automatic caching and request deduplication
- Background data refetching and optimistic updates
- Declarative data fetching vs manual state management

---

## 🐳 Docker Architecture

### Container Images

All services are containerized using **multi-stage builds** and **Alpine Linux** base images for optimal size:

| Service | Image Size | Build Type |
|---------|------------|------------|
| **Backend** | 232 MB | Multi-stage Python (slim → alpine) |
| **Frontend** | 63 MB | Multi-stage Node → Nginx |
| **Bot** | 229 MB | Python slim (includes OpenAI SDK) |
| **Scraper** | 194 MB | Python slim (httpx + BS4) |
| **PostgreSQL** | 274 MB | Official `postgres:15-alpine` |

**Total stack size: ~992 MB** (less than 1GB for entire application)

### Why Images Are Small

✅ **Multi-stage builds** - Build dependencies are discarded, only runtime artifacts remain  
✅ **Alpine Linux** - Minimal base images (~5MB vs ~100MB for Ubuntu)  
✅ **No build tools** - `gcc`, `make`, `npm` excluded from final images  
✅ **Layer caching** - Docker reuses unchanged layers across builds  
✅ **Optimized dependencies** - Only production packages included

### Finding Docker Images

```bash
# List all project images
docker images | grep auto-assistent-llm

# List all images including base images
docker images

# Check PostgreSQL image (official, not prefixed with project name)
docker images postgres
```

**Note:** PostgreSQL image (`postgres:15-alpine`) is an official Docker Hub image, not built by this project. It appears without the `auto-assistent-llm` prefix.

---

## ✨ Features

### 🎨 Responsive Admin Dashboard
- **Desktop**: Ant Design `<Table>` with sortable columns, fixed headers
- **Mobile**: `<List>` with `<Card>` components for touch-friendly interaction
- **Automatic layout switching** based on screen size (breakpoint: `md` = 768px)

### ♾️ Infinite Scroll Pagination
- **Cursor-based loading** - fast performance on large datasets
- **Intersection Observer API** - triggers `fetchNextPage()` when bottom element enters viewport
- **Loading states** - skeleton screens and spinners for better UX
- **End detection** - "All cars loaded" indicator when no more data

### 🔍 Server-Side Search
- **Debounced input** - 500ms delay to avoid excessive API calls
- **SQL ILIKE queries** - searches across `brand`, `model`, and `color` columns
- **Real-time results counter** - "Found 1,234 results"
- **Pagination-aware** - search maintains cursor position

### 🤖 LLM-Powered Telegram Bot
- **Natural language processing** - "Show me red Toyotas under ¥2M from 2020"
- **OpenAI GPT-4o-mini** - extracts structured filters from user queries
- **Dynamic SQL generation** - converts JSON filters to SQLAlchemy queries
- **Inline results** - sends car listings with clickable links

### 🔒 Secure Authentication
- **JWT tokens** - stateless authentication with 60-minute expiry
- **bcrypt password hashing** - industry-standard with 12 rounds
- **HTTP-only cookies** - prevents XSS attacks (configurable)
- **Protected routes** - unauthorized access returns 401

### 🐳 Production-Ready Docker
- **Multi-stage builds** - final images are 80% smaller
- **Non-root users** - all services run as unprivileged users
- **Health checks** - automatic container restarts on failure
- **Automatic migrations** - `entrypoint.sh` runs Alembic on startup
- **Single command deployment** - `docker-compose up -d`

---

## 🛠 Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11 | Runtime environment |
| **FastAPI** | 0.100+ | Async REST API framework |
| **SQLAlchemy** | 2.0 | ORM with async support |
| **Alembic** | 1.12+ | Database migrations |
| **asyncpg** | 0.28+ | PostgreSQL async driver |
| **Pydantic** | 2.0+ | Data validation |
| **python-jose** | 3.3+ | JWT token generation |
| **bcrypt** | 4.1.2 | Password hashing |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19 | UI framework |
| **TypeScript** | 5.9 | Type safety |
| **Vite** | 7.3 | Build tool & dev server |
| **Ant Design** | 6.3+ | Component library |
| **TanStack Query** | 5.90+ | Server state management |
| **Zustand** | 4.5+ | Client state (auth) |
| **Axios** | 1.6+ | HTTP client |
| **Tailwind CSS** | 3.4+ | Utility-first CSS |

### Scraper
| Technology | Version | Purpose |
|------------|---------|---------|
| **httpx** | 0.27+ | Async HTTP requests |
| **BeautifulSoup4** | 4.12+ | HTML parsing |
| **SQLAlchemy** | 2.0 | Data persistence |

### Telegram Bot
| Technology | Version | Purpose |
|------------|---------|---------|
| **aiogram** | 3.4+ | Telegram Bot API |
| **OpenAI SDK** | 1.14+ | LLM integration (GPT-4) |
| **SQLAlchemy** | 2.0 | Database queries |

### Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 15-alpine | Primary database |
| **Docker** | 20.10+ | Containerization |
| **Docker Compose** | 2.0+ | Multi-container orchestration |
| **Nginx** | stable-alpine | Frontend web server |

---

## 📊 Project Structure

```
auto-assistent-llm/
├── backend/                  # FastAPI application
│   ├── alembic/              # Database migrations
│   ├── auth.py               # JWT & bcrypt utilities
│   ├── database.py           # SQLAlchemy async engine
│   ├── main.py               # FastAPI app & routes
│   ├── models.py             # ORM models (User, Car)
│   ├── schemas.py            # Pydantic schemas
│   ├── seed.py               # Admin user seeder
│   ├── entrypoint.sh         # Docker init script
│   ├── Dockerfile            # Multi-stage Python build
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── api/              # Axios client
│   │   ├── components/       # React components
│   │   │   ├── CarsTable.tsx # Main table/list
│   │   │   └── ui/           # Reusable UI components
│   │   ├── features/
│   │   │   └── auth/         # Login form
│   │   ├── hooks/            # Custom hooks (useCars)
│   │   ├── store/            # Zustand store
│   │   ├── types/            # TypeScript interfaces
│   │   └── App.tsx           # Root component
│   ├── nginx.conf            # Production Nginx config
│   ├── Dockerfile            # Multi-stage Node + Nginx
│   └── package.json          # NPM dependencies
│
├── scraper/                  # Web scraper worker
│   ├── main.py               # httpx + BeautifulSoup4
│   ├── database.py           # Shared DB connection
│   ├── models.py             # Shared ORM models
│   ├── Dockerfile            # Python slim build
│   └── requirements.txt      # Scraper dependencies
│
├── bot/                      # Telegram bot
│   ├── main.py               # aiogram + OpenAI
│   ├── database.py           # Shared DB connection
│   ├── models.py             # Shared ORM models
│   ├── Dockerfile            # Python slim build
│   └── requirements.txt      # Bot dependencies
│
├── docker-compose.yml        # Orchestration config
├── .env.example              # Environment template
├── DOCKER.md                 # Deployment guide
└── README.md                 # This file
```

---

## 📝 Development

### Local Development (without Docker)

**Prerequisites:**
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) - fast Python package manager
- Install [PostgreSQL 15+](https://www.postgresql.org/download/) and create database

**Setup:**

1. **Create PostgreSQL database:**
```bash
psql -U postgres
CREATE DATABASE auto_assistent;
CREATE USER auto_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE auto_assistent TO auto_user;
\q
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and change:
# DATABASE_URL=postgresql+asyncpg://auto_user:your_password@localhost:5432/auto_assistent
# (use 'localhost' instead of 'db' for local development)
```

3. **Run services:**

```bash
# Backend
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn main:app --reload

# Frontend (in separate terminal)
cd frontend
npm install
npm run dev

# Scraper (in separate terminal)
cd scraper
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python main.py

# Bot (in separate terminal)
cd bot
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python main.py
```

**Local Database Migrations:**
```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

### Docker Development

**Database Migrations:**

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

**Logs & Debugging:**

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Access container shell
docker-compose exec backend sh
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [carsensor.net](https://www.carsensor.net/) - Data source
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python framework
- [Ant Design](https://ant.design/) - React component library
- [TanStack Query](https://tanstack.com/query) - Powerful data synchronization

---

## 🔒 Security

**Important Security Practices:**

- **Never commit your `.env` file** to version control - it contains sensitive credentials
- Always use the provided `.env.example` as a template
- Generate strong passwords and secrets for production deployment
- Rotate JWT secrets and API keys regularly
- Use environment-specific configurations for development, staging, and production

**Included in `.gitignore`:**
```
.env
*.log
__pycache__/
*.pyc
node_modules/
```

---

## ⚠️ Disclaimer

**This project is provided for educational and demonstration purposes only.**

By using this software, you agree to the following:

1. **Educational Purpose**: This project is a technical demonstration of modern web development practices, microservices architecture, and data processing techniques.

2. **Web Scraping Compliance**: The web scraper component is designed to work with publicly available data. Users **must**:
   - Review and comply with the target website's `robots.txt` file
   - Respect the website's Terms of Service (ToS)
   - Implement appropriate rate limiting to avoid overloading servers
   - Obtain explicit permission from website owners when required

3. **No Warranty**: This software is provided "as is" without warranty of any kind. See the [LICENSE](LICENSE) file for details.

4. **User Responsibility**: Users are solely responsible for ensuring their use of this software complies with all applicable laws, regulations, and website policies in their jurisdiction.

5. **Data Usage**: Any data collected must be used ethically and in compliance with applicable data protection regulations (GDPR, CCPA, etc.).

**The author and contributors are not responsible for any misuse of this software.**

