# Domain Finder Pro - Deployment Guide

Complete guide to deploy Domain Finder Pro to production.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [GitHub Actions Setup](#github-actions-setup)
5. [Production Checklist](#production-checklist)

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- pip

### Setup

1. **Clone repository**
```bash
git clone <your-repo>
cd domain-finder-pro
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r backend/requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database URL and API keys
```

5. **Initialize database**
```bash
cd backend
python -c "from database import init_db; init_db()"
```

6. **Run development server**
```bash
cd backend
uvicorn main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

7. **Open frontend**
```bash
# In another terminal
cd frontend
python -m http.server 8080
# Visit http://localhost:8080
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Start services**
```bash
docker-compose up -d
```

Services will start:
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Frontend: http://localhost:80 (if nginx profile enabled)

2. **View logs**
```bash
docker-compose logs -f backend
```

3. **Stop services**
```bash
docker-compose down
```

### Using Docker Only

1. **Build image**
```bash
docker build -t domain-finder-pro:latest .
```

2. **Run container**
```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e APIFY_TOKEN=... \
  --name domain-finder \
  domain-finder-pro:latest
```

---

## Cloud Deployment

### Option 1: Vercel + Supabase + GitHub Actions

**Cost: ~$10-25/month**

#### Frontend (Vercel)

1. **Connect GitHub**
   - Go to [vercel.com](https://vercel.com)
   - Connect your GitHub repository
   - Import project

2. **Configure**
   - Root directory: `frontend`
   - Build command: (leave empty)
   - Output directory: (leave empty)

3. **Deploy**
```bash
vercel deploy --prod
```

Frontend URL: `https://your-project.vercel.app`

#### Backend (Supabase + Cloud Run)

1. **Create Supabase project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Copy database connection string

2. **Deploy to Cloud Run**
```bash
# Install Google Cloud SDK
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/domain-finder

# Deploy
gcloud run deploy domain-finder \
  --image gcr.io/YOUR_PROJECT_ID/domain-finder \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-env-vars APIFY_TOKEN=... \
  --allow-unauthenticated
```

Backend URL: `https://domain-finder-xxxxx.run.app`

3. **Update frontend API URL**
   - Settings tab in dashboard
   - Set to Cloud Run URL

#### Scheduled Scraping (GitHub Actions)

1. **Add secrets to GitHub**
   - Go to Settings → Secrets and variables → Actions
   - Add:
     - `DB_PASSWORD`
     - `APIFY_TOKEN`
     - `SENDGRID_API_KEY`
     - `SLACK_WEBHOOK`

2. **Workflow runs automatically**
   - Every day at 9 AM UTC
   - Or manually via: Actions → Daily Domain Scrape → Run workflow

### Option 2: DigitalOcean App Platform

**Cost: ~$12/month**

1. **Deploy via CLI**
```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create app
doctl apps create --spec app.yaml
```

2. **app.yaml configuration**
```yaml
name: domain-finder-pro
services:
- name: backend
  github:
    repo: your-username/domain-finder-pro
    branch: main
  build_command: pip install -r backend/requirements.txt
  run_command: cd backend && uvicorn main:app --host 0.0.0.0 --port 8080
  http_port: 8080
  envs:
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
    value: postgresql://...
  - key: APIFY_TOKEN
    scope: RUN_AND_BUILD_TIME
    value: ${APIFY_TOKEN}
```

### Option 3: Self-Hosted DigitalOcean Droplet

**Cost: ~$6/month**

1. **Create droplet**
   - OS: Ubuntu 22.04 LTS
   - Size: 1GB RAM, 1vCPU
   - Region: Closest to you

2. **SSH into droplet**
```bash
ssh root@your-droplet-ip
```

3. **Install dependencies**
```bash
apt update && apt install -y python3.11 python3-pip postgresql postgresql-contrib nginx

# Start services
systemctl start postgresql
systemctl start nginx
```

4. **Deploy application**
```bash
# Clone repo
git clone your-repo /home/domain-finder-pro
cd /home/domain-finder-pro/backend

# Install Python packages
pip install -r requirements.txt

# Configure environment
nano .env  # Set your configuration

# Initialize database
python3 -c "from database import init_db; init_db()"

# Install systemd service
sudo nano /etc/systemd/system/domain-finder.service
```

5. **Systemd service file**
```ini
[Unit]
Description=Domain Finder Pro API
After=postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/domain-finder-pro/backend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m gunicorn main:app --workers 4 --bind 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

6. **Configure Nginx reverse proxy**
```nginx
# /etc/nginx/sites-available/domain-finder
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable
ln -s /etc/nginx/sites-available/domain-finder /etc/nginx/sites-enabled/
systemctl restart nginx
```

7. **Setup SSL (Let's Encrypt)**
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

## GitHub Actions Setup

### 1. Configure Secrets

Settings → Secrets and variables → Actions:

```
DB_PASSWORD        - PostgreSQL password
APIFY_TOKEN        - Apify API token
SENDGRID_API_KEY   - SendGrid API key
SLACK_WEBHOOK      - Slack webhook URL
WHOIS_JSON_API_KEY - WhoisJSON API key
```

### 2. Workflow Triggers

**Automatic (9 AM UTC daily)**
```yaml
schedule:
  - cron: '0 9 * * *'
```

**Manual trigger**
- GitHub Actions → Daily Domain Scrape → Run workflow

### 3. Monitor runs
- GitHub Actions tab
- Check logs and status
- Slack notifications on success/failure

---

## Environment Variables

### Required
```env
DATABASE_URL=postgresql://user:pass@host:5432/db_name
```

### Optional
```env
APIFY_TOKEN=                    # Apify API token for scraping
SENDGRID_API_KEY=               # SendGrid for email alerts
SLACK_WEBHOOK=                  # Slack webhook for notifications
WHOIS_JSON_API_KEY=             # WhoisJSON API key
DEBUG=False                      # Set True for development
HOST=0.0.0.0
PORT=8000
SCRAPER_ENABLED=True
SCRAPER_TIME=09:00
ALERT_EMAIL=your-email@example.com
MIN_QUALITY_SCORE=70
TOP_DOMAINS_COUNT=20
USE_SAMPLE_DATA=False           # Use sample data if True
```

---

## Database Setup

### Supabase (Free tier)
1. Create project at supabase.com
2. Get connection string from Settings
3. Copy to DATABASE_URL in .env

### Self-hosted PostgreSQL
```bash
createdb domain_finder
psql domain_finder < schema.sql
```

### Manual schema
```sql
-- The application will auto-create tables via SQLAlchemy
-- Just need empty database
```

---

## Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificate installed
- [ ] CORS origins configured for production domain
- [ ] API rate limiting enabled
- [ ] Logging configured
- [ ] Monitoring setup (New Relic, DataDog, etc.)
- [ ] Backups configured
- [ ] DNS records updated
- [ ] Firewall rules configured
- [ ] GitHub Actions secrets configured
- [ ] Scheduled scraping tested
- [ ] Email alerts tested
- [ ] Slack notifications tested
- [ ] Frontend API URL updated
- [ ] Load testing performed
- [ ] Security audit completed
- [ ] Documentation updated

---

## Troubleshooting

### Database connection error
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check PostgreSQL status
systemctl status postgresql
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Scheduler not running
```bash
# Check scheduler status
curl http://localhost:8000/api/scheduler/status

# Manually trigger scrape
curl -X POST http://localhost:8000/api/admin/manual-scrape
```

### Memory issues
```bash
# Check container memory
docker stats domain-finder

# Increase memory in docker-compose
memory: 2g
```

---

## Cost Breakdown

| Service | Monthly | Purpose |
|---------|---------|---------|
| Supabase DB | $5-25 | PostgreSQL database |
| Vercel (Frontend) | $0-20 | Frontend hosting |
| Google Cloud Run | $5-10 | API hosting |
| Apify (Scraping) | $2-5 | Domain scraping |
| SendGrid | $0 | Email (1000 free/month) |
| **TOTAL** | **$12-60** | |

---

## Scaling

### More scraping capacity
- Increase Apify plan ($10+/month)
- Batch domains in smaller sets
- Distribute across multiple schedulers

### More traffic
- Add more Cloud Run instances (auto-scaling)
- Enable caching headers
- Use CDN for static files

### Database growth
- Enable PostgreSQL backups
- Archive old records
- Implement data retention policy

---

## Support

For issues:
- Check GitHub Issues
- Review logs: `docker-compose logs`
- Test API: `curl http://localhost:8000/health`
- Review documentation: `/docs` endpoint

---

Last updated: 2025-02-26
