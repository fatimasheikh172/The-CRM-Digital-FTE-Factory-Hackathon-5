# Railway Deployment Guide

## Overview

This guide covers deploying the TechCorp Customer Success FTE to Railway.app.

## Prerequisites

- GitHub account
- Railway account (free tier available)
- Google Gemini API key

## Steps

### 1. Push to GitHub

Ensure your code is pushed to a GitHub repository:

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Connect Railway to GitHub

1. Go to [Railway](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### 3. Add PostgreSQL Plugin

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provision a PostgreSQL instance
4. The `DATABASE_URL` environment variable will be set automatically

### 4. Set Environment Variables

In Railway dashboard, go to Variables and add:

```bash
# Required
GEMINI_API_KEY=your_google_gemini_api_key
ENVIRONMENT=production
LOG_LEVEL=INFO
DEMO_MODE=false

# Optional (Railway provides DATABASE_URL automatically)
# DATABASE_URL is auto-set by Railway PostgreSQL plugin
```

### 5. Deploy

Railway will automatically deploy when you push to your main branch.

Manual deploy:
1. Go to your service in Railway
2. Click "Deploy" → "Deploy Manually"
3. Select your branch

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `DATABASE_URL` | PostgreSQL connection (auto-set by Railway) | Auto |
| `ENVIRONMENT` | Environment name (production/staging) | No |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/WARNING) | No |
| `DEMO_MODE` | Enable demo mode without database (true/false) | No |

## Database

Railway automatically provides `DATABASE_URL` when you add the PostgreSQL plugin.

The application supports both:
- **Railway**: Uses `DATABASE_URL` environment variable
- **Local**: Uses individual variables (`DB_HOST`, `DB_PORT`, etc.)

No manual PostgreSQL configuration needed!

## Kafka Handling

Kafka is complex to set up on Railway. The application includes a fallback:

- **If Kafka is available**: Uses real Kafka for event streaming
- **If Kafka is unavailable**: Falls back to in-memory queue

The API will work without Kafka - it logs a warning but continues running.

## Health Check

Railway will use the `/health` endpoint for health checks:

- **Path**: `/health`
- **Timeout**: 300 seconds
- **Expected response**: HTTP 200 with status

## Accessing Your App

After deployment, Railway provides a URL:

```
https://your-app-name.railway.app
```

## Troubleshooting

### Build Fails

Check the build logs in Railway. Common issues:
- Missing dependencies in `requirements.txt`
- Python version mismatch (use Python 3.11)

### App Won't Start

Check the runtime logs:
1. Go to your service in Railway
2. Click "Deployments"
3. View logs for the latest deployment

Common issues:
- Missing `GEMINI_API_KEY`
- Database connection issues (check `DATABASE_URL`)

### Database Connection Issues

Verify PostgreSQL is running:
1. Check the PostgreSQL plugin is active
2. Verify `DATABASE_URL` is set in Variables
3. Check database logs in Railway

## Local Testing

Test locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/health
```

## Files Created for Railway

| File | Purpose |
|------|---------|
| `Procfile` | Process configuration |
| `runtime.txt` | Python version (3.11.0) |
| `railway.json` | Railway-specific config |
| `nixpacks.toml` | Nixpacks build configuration |
| `requirements.txt` | Production dependencies |
| `requirements-dev.txt` | Development dependencies |

## Support

For Railway-specific issues, see [Railway Docs](https://docs.railway.app).
