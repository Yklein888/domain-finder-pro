# 🌐 Domain Finder Pro

**Automated Domain Discovery & Investment Analysis Tool**

Discover, analyze, and track high-potential domains for investment. Automated daily scanning of expired domains with intelligent scoring, ROI estimation, and portfolio management.

---

## 🎯 Features

✅ **Daily Automated Scanning** - Runs every morning at 9 AM UTC
✅ **Intelligent Scoring Algorithm** - 0-100 domain quality scoring
✅ **ROI Estimation** - Predicts profit potential (3x-1000x ROI)
✅ **Backlink Analysis** - RDAP + WhoisJSON integration
✅ **Portfolio Management** - Track purchased domains and ROI
✅ **CSV Export** - Download portfolio data anytime
✅ **Email/Slack Alerts** - Daily digest of top opportunities
✅ **Web Dashboard** - Real-time opportunity viewer

---

## 📊 Cost Breakdown

| Service | Cost/Month | Purpose |
|---------|-----------|---------|
| DigitalOcean VPS | $6 | Hosting |
| Apify (Scraping) | $2-5 | ExpiredDomains |
| APIs | $0 | RDAP, WhoisJSON, Wayback |
| **TOTAL** | **$8-11/month** | |

**vs Competitors:**
- Domain Hunter Gatherer: $197-297/month
- DomCop: $50+/month
- **Domain Finder Pro: $8-11/month** ✅

---

## 🚀 Tech Stack

- **Backend:** FastAPI 0.104+ with Uvicorn/Gunicorn
- **Database:** PostgreSQL 15+ (Supabase/DigitalOcean/Self-hosted)
- **ORM:** SQLAlchemy 2.0 with Pydantic 2.0
- **Scheduling:** APScheduler (daily scraping, cleanup jobs)
- **Scraping:** Apify API (production) + local sample data
- **APIs:** RDAP (free), WhoisJSON (1000 free calls/month), Wayback Machine
- **Frontend:** Vanilla HTML/CSS/JavaScript with Bootstrap 5
- **Reverse Proxy:** Nginx
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions (scheduled workflows)
- **Deployment:** Vercel, Google Cloud Run, DigitalOcean, self-hosted
- **Notifications:** SendGrid (email), Slack (webhooks)

---

## 🛠️ Quick Start

### Local Development (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/domain-finder-pro.git
cd domain-finder-pro

# Option 1: Docker Compose (easiest)
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:8080 (or open frontend/index.html)

# Option 2: Manual setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit ../.env with your database URL and API keys

# Initialize database
python -c "from database import init_db; init_db()"

# Run backend server
uvicorn main:app --reload
# API docs: http://localhost:8000/docs

# In another terminal, serve frontend
cd ../frontend
python -m http.server 8080
# Dashboard: http://localhost:8080
```

### Production Deployment

```bash
# See DEPLOYMENT.md for detailed instructions
# Quick options:
# - Vercel (frontend) + Cloud Run (backend)
# - DigitalOcean App Platform
# - Self-hosted DigitalOcean Droplet
# - Docker on any cloud provider
```

---

## 📋 Implementation Status

### Week 1: Backend Foundation ✅ COMPLETED
- [x] FastAPI setup with lifespan management
- [x] PostgreSQL models (Domain, PortfolioItem, Alert, DomainScore)
- [x] Database layer with connection pooling
- [x] Pydantic API schemas with validation
- [x] Health check endpoints
- [x] CRUD endpoints for domains and portfolio

### Week 2: Scraper & Analysis ✅ COMPLETED
- [x] Domain Scorer: 0-100 intelligent scoring (6 factors)
- [x] Backlink Analyzer: RDAP + WhoisJSON + Wayback Machine
- [x] Apify scraper with sample data fallback
- [x] APScheduler: Daily 9 AM UTC + weekly cleanup
- [x] Comprehensive test suite with sample data

### Week 3: API Routes & Integration ✅ COMPLETED
- [x] Domain endpoints (list, top, details, add)
- [x] Portfolio endpoints (CRUD, summary, stats)
- [x] CSV export endpoints (3 formats)
- [x] Scoring service orchestration
- [x] Alert service (Email + Slack)
- [x] Error handling and validation

### Week 4: Frontend Dashboard ✅ COMPLETED
- [x] Responsive HTML/CSS/JS dashboard
- [x] Top opportunities view with filters
- [x] Portfolio manager with CRUD
- [x] CSV export interface (3 formats)
- [x] Settings and API configuration
- [x] Real-time stats and metrics
- [x] Mobile-optimized design

### Week 5: Automation & Deployment ✅ COMPLETED
- [x] GitHub Actions workflow (daily at 9 AM UTC)
- [x] Docker & Docker Compose setup
- [x] Production deployment guide
- [x] Nginx reverse proxy configuration
- [x] Multiple deployment options
- [x] Environment configuration templates
- [x] Scaling and troubleshooting guides

---

## 📖 Documentation

- [API Documentation](./docs/API.md) - Detailed endpoint reference
- [Database Schema](./docs/SCHEMA.md) - Database design
- [Deployment Guide](./docs/DEPLOYMENT.md) - Production setup
- [Scoring Algorithm](./docs/SCORING.md) - How domains are scored

---

## 🎓 Domain Flipping Basics

### Scoring Factors (0-100)
- Age (0-20): Older domains = higher authority
- Backlinks (0-25): Quality/quantity of pointing domains
- Authority (0-20): Domain Authority estimation
- Brandability (0-15): Memorability & pronounceability
- Keywords (0-15): High-value keyword presence
- Traffic (0-5): Historical visitor indicators

### Price Estimates
- **Grade A** (85-100): $10,000 - $100,000
- **Grade B** (70-84): $2,000 - $15,000
- **Grade C** (55-69): $500 - $3,000
- **Grade D** (40-54): $100 - $600
- **Grade E** (25-39): $20 - $150
- **Grade F** (0-24): $5 - $25

### ROI Examples
- Professional average: 22% per domain
- Individual flips: 3x - 1000x ROI potential
- Full-time income: $100,000+/year possible

---

## 📈 Market Data

- **Market Size:** $1.2 billion in domain sales (2024)
- **Average Transaction:** $142,131
- **Beginner Profit:** $100-$300 per flip
- **Experienced Profit:** $500-$2,000+ per flip
- **Best Marketplaces:** Flippa, Sedo, Afternic

---

## 🔗 Resources

- [NameBio](https://namebio.com) - Comps database ($49 lifetime)
- [Ahrefs](https://ahrefs.com) - Backlink analysis (free version)
- [WhoisJSON](https://whoisjson.com) - WHOIS API (1000 free/month)
- [Apify](https://apify.com) - Web scraping ($2-5/month)
- [Flippa](https://flippa.com) - Domain marketplace (10% commission)
- [Sedo](https://sedo.com) - Domain marketplace (15-20% commission)
- [Afternic](https://afternic.com) - Via GoDaddy (15-25% commission)

---

## 📞 Support & Contributing

For issues, questions, or contributions, please:
- Open a GitHub Issue
- Submit a Pull Request
- Review Documentation

---

*Built with ❤️ for domain investors everywhere*
