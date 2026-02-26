#!/bin/bash

# Domain Finder Pro - Cloud Run Deployment Script
# יוצר ומפרסם את האפליקציה ל-Google Cloud Run

set -e  # Exit on error

echo "🚀 Domain Finder Pro - Cloud Run Deployment"
echo "==========================================="

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get GCP Project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project set. Run: gcloud config set project PROJECT_ID"
    exit 1
fi

echo "✅ Project: $PROJECT_ID"

# Enable required APIs
echo "📡 Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    build.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    cloudscheduler.googleapis.com

# Build Docker image
echo "🔨 Building Docker image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/domain-finder-pro:latest \
    --timeout=1800s

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."

# Ask for Database URL
read -p "Enter Supabase DATABASE_URL: " DATABASE_URL

gcloud run deploy domain-finder-pro \
    --image gcr.io/$PROJECT_ID/domain-finder-pro:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 120 \
    --max-instances 10 \
    --set-env-vars "DATABASE_URL=$DATABASE_URL,APIFY_TOKEN=$(grep APIFY /Users/yitzi/.claude/projects/*/memory/MEMORY.md | tail -1)" \
    --no-gen2

# Get service URL
SERVICE_URL=$(gcloud run services describe domain-finder-pro --platform managed --region us-central1 --format 'value(status.url)')

echo ""
echo "✅✅✅ Deployment Successful!"
echo "================================"
echo "🌐 Backend URL: $SERVICE_URL"
echo "📚 API Docs: $SERVICE_URL/docs"
echo "❤️  Health Check: $SERVICE_URL/health"
echo ""
echo "Next steps:"
echo "1. Update frontend API URL to: $SERVICE_URL"
echo "2. Deploy frontend to Vercel"
echo "3. Monitor logs: gcloud run logs read domain-finder-pro --limit 50"
