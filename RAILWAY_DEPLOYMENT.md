# Railway Deployment Guide

Complete guide for deploying the Tally Webhook Workflow to Railway.

## Overview

This guide covers deploying the market research automation system to Railway, a modern platform that simplifies deployment with:
- ✅ Automatic HTTPS
- ✅ Auto-scaling
- ✅ Built-in monitoring
- ✅ Simple environment variable management
- ✅ GitHub integration

## Prerequisites

- Railway account (https://railway.app)
- GitHub account (for repo connection)
- All required API keys ready:
  - OpenRouter API key
  - Valyu API key
  - Slack Bot Token
  - Tally Webhook Secret

## Deployment Steps

### 1. Prepare Repository

Ensure your repository has these files:
```
✅ Dockerfile
✅ .dockerignore
✅ railway.json
✅ requirements.txt
✅ app.py
✅ All source code
```

Commit and push to GitHub:
```bash
git add Dockerfile .dockerignore railway.json
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository: `enterpirse-deepsearch`
6. Railway will automatically detect the Dockerfile

### 3. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

#### Required: LLM Configuration

```env
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-sonnet-4
OPENROUTER_API_KEY=sk-or-v1-xxxx
```

Optional OpenRouter tracking:
```env
OPENROUTER_SITE_URL=https://your-domain.railway.app
OPENROUTER_SITE_NAME=Market Research Bot
```

#### Required: Web Research

```env
VALYU_API_KEY=your_valyu_api_key_here
```

#### Required: Research Configuration

```env
MAX_WEB_RESEARCH_LOOPS=10
FETCH_FULL_PAGE=True
INCLUDE_RAW_CONTENT=True
```

#### Required: Activity Generation

```env
ENABLE_ACTIVITY_GENERATION=true
ACTIVITY_VERBOSITY=medium
ACTIVITY_LLM_PROVIDER=openrouter
ACTIVITY_LLM_MODEL=anthropic/claude-sonnet-4
```

#### Required: Tally Integration

```env
TALLY_WEBHOOK_SECRET=whsec_your_secret_here
```

#### Required: Slack Integration

```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_DEFAULT_CHANNEL=#marketing-research
```

#### Optional: LangSmith Tracing

```env
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_ENDPOINT=
LANGCHAIN_PROJECT=
```

### 4. Deploy

Railway will automatically:
1. Build the Docker image
2. Deploy the container
3. Assign a public URL (e.g., `https://your-app.railway.app`)
4. Start health checks

Monitor deployment in the **Deployments** tab.

### 5. Verify Deployment

#### Check API Status

```bash
curl https://your-app.railway.app/
```

Expected response:
```json
{
  "message": "Deep Research API is running",
  "version": "v0.6.5",
  "endpoints": {
    "POST /api/tally/webhook": "Receive Tally form submissions and trigger workflow",
    ...
  }
}
```

#### Check Health Endpoint

Railway automatically monitors: `GET /` for health checks.

#### View Logs

In Railway dashboard:
1. Go to **Deployments** tab
2. Click on latest deployment
3. View live logs

### 6. Configure Tally Webhook

Now that your app is deployed, configure Tally:

1. Open your Tally form
2. Go to **Integrations** → **Webhooks**
3. Add webhook URL: `https://your-app.railway.app/api/tally/webhook`
4. Copy the **Webhook Secret**
5. Update Railway environment variable: `TALLY_WEBHOOK_SECRET`
6. Click **"Redeploy"** in Railway to apply changes

### 7. Configure Slack App

If not already done:

1. Go to https://api.slack.com/apps
2. Create app: "Marketing Research Bot"
3. Add OAuth Scopes:
   - `chat:write`
   - `files:write`
   - `channels:read`
4. Install to workspace
5. Copy Bot Token
6. Update Railway environment variable: `SLACK_BOT_TOKEN`
7. Click **"Redeploy"** in Railway

### 8. Test the Integration

Submit a test form via Tally and verify:

1. **Railway Logs** - Check for incoming webhook
   ```
   Received Tally webhook: event_type=FORM_RESPONSE
   ```

2. **Slack Channel** - Should receive start notification
   ```
   🚀 Market Research Workflow Started
   ```

3. **Workflow Status** - Check via API
   ```bash
   curl https://your-app.railway.app/api/tally/workflows
   ```

4. **Slack Delivery** - After 10-15 minutes, should receive PDF

## Railway Configuration Details

### Dockerfile Explained

The Dockerfile includes:

```dockerfile
# Base image: Python 3.11 slim for smaller size
FROM python:3.11-slim

# System dependencies for:
# - PDF generation (ReportLab)
# - Image processing (OpenCV, PIL)
# - Audio/video processing (FFmpeg)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    ffmpeg \
    ...

# Install Python dependencies
RUN pip install -r requirements.txt

# Railway sets PORT automatically
ENV PORT=8000

# Run with uvicorn (2 workers for concurrency)
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 2
```

### Resource Requirements

**Recommended Railway Plan:**
- **Starter Plan** or higher
- **RAM:** 1GB minimum (2GB recommended)
- **CPU:** 1 vCPU minimum
- **Storage:** 1GB (for PDF outputs)

### Environment Variables on Railway

Railway automatically provides:
- `PORT` - Application port (usually 8000)
- `RAILWAY_ENVIRONMENT` - Deployment environment
- `RAILWAY_PROJECT_ID` - Project identifier
- `RAILWAY_SERVICE_ID` - Service identifier

Your app uses `PORT` to bind correctly:
```python
# Railway sets this automatically
port = int(os.environ.get("PORT", 8000))
```

## Monitoring & Maintenance

### View Logs

**Real-time logs:**
1. Railway Dashboard → **Deployments**
2. Click latest deployment
3. Live log stream

**Search logs:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# View logs
railway logs

# Follow logs
railway logs --follow
```

### Monitor Workflows

**Check active workflows:**
```bash
curl https://your-app.railway.app/api/tally/workflows?limit=20
```

**Check specific workflow status:**
```bash
curl https://your-app.railway.app/api/tally/workflow/{workflow_id}/status
```

### Railway Metrics

Railway provides built-in metrics:
- CPU usage
- Memory usage
- Network traffic
- Request rate
- Error rate

Access in Dashboard → **Metrics** tab

## Scaling Configuration

### Horizontal Scaling (Multiple Instances)

Edit `railway.json`:
```json
{
  "deploy": {
    "numReplicas": 2  // Run 2 instances
  }
}
```

**Note:** For multiple instances, consider:
- Using a database instead of file storage
- Implementing distributed locking
- Session management for workflow state

### Vertical Scaling (More Resources)

Railway automatically scales resources based on usage.

For consistent high load:
1. Go to **Settings** → **Resources**
2. Adjust memory/CPU limits
3. Click **"Save"**

## Custom Domain (Optional)

### Add Custom Domain

1. Railway Dashboard → **Settings**
2. Click **"Add Custom Domain"**
3. Enter your domain: `api.yourdomain.com`
4. Railway provides DNS records:
   ```
   Type: CNAME
   Name: api
   Value: your-app.railway.app
   ```
5. Add CNAME to your DNS provider
6. Wait for DNS propagation (5-30 minutes)

### Update Tally Webhook URL

After custom domain is active:
1. Update Tally webhook: `https://api.yourdomain.com/api/tally/webhook`
2. Update environment variable: `OPENROUTER_SITE_URL=https://api.yourdomain.com`
3. Redeploy on Railway

## Troubleshooting

### Build Failures

**Error: Python dependencies failed**
```
Solution:
1. Check requirements.txt syntax
2. Verify all packages are available
3. Check Railway build logs for specific error
```

**Error: System dependencies missing**
```
Solution:
1. Check Dockerfile apt-get packages
2. Verify package names are correct
3. Test build locally: docker build -t test .
```

### Deployment Failures

**Error: Health check timeout**
```
Solution:
1. Increase healthcheckTimeout in railway.json
2. Verify app starts correctly (check logs)
3. Ensure PORT environment variable is used
```

**Error: Container crashes on startup**
```
Solution:
1. Check Railway logs for error message
2. Verify all environment variables are set
3. Test locally with: docker run -p 8000:8000 test
```

### Runtime Issues

**Webhook not receiving requests**
```
Solution:
1. Verify Tally webhook URL is correct
2. Check TALLY_WEBHOOK_SECRET matches
3. Review Railway logs for incoming requests
4. Test with: curl -X POST https://your-app.railway.app/api/tally/test
```

**Slack notifications not working**
```
Solution:
1. Verify SLACK_BOT_TOKEN is correct
2. Check bot has required scopes
3. Ensure bot is added to channel
4. Test Slack API: railway logs | grep "Slack"
```

**PDF generation failing**
```
Solution:
1. Check Railway logs for ReportLab errors
2. Verify filesystem permissions (should be OK in Railway)
3. Check outputs/pdfs directory exists
```

**Memory issues / OOM errors**
```
Solution:
1. Increase Railway memory limit (Settings → Resources)
2. Reduce MAX_WEB_RESEARCH_LOOPS
3. Optimize workflow to use less memory
```

### Railway CLI Troubleshooting

```bash
# Check service status
railway status

# View environment variables
railway variables

# Restart service
railway restart

# Open service in browser
railway open

# SSH into container (for debugging)
railway run bash
```

## Cost Optimization

### Reduce Railway Costs

1. **Use Starter Plan** ($5/month for hobby projects)
2. **Optimize Build Time**
   - Use .dockerignore to exclude unnecessary files
   - Leverage Docker layer caching
3. **Reduce Memory Usage**
   - Lower MAX_WEB_RESEARCH_LOOPS if possible
   - Use single worker if traffic is low
4. **Monitor Usage**
   - Check Railway dashboard for resource usage
   - Optimize code based on metrics

### Resource Usage Estimates

**Per Workflow:**
- CPU: 10-30% during execution
- Memory: 300-500 MB
- Storage: ~2-5 MB per PDF
- Network: ~50-100 MB (API calls)

**Monthly Estimates (50 workflows/month):**
- Storage: ~250 MB
- Network: ~5 GB
- Compute: ~2-3 hours CPU time

## Backup & Recovery

### Backup Workflow Data

Workflow data is stored in:
```
outputs/
├── pdfs/       # Generated PDFs
└── workflows/  # JSON state files
```

**Automated Backup (Optional):**
1. Use Railway Volume for persistent storage
2. Set up periodic backups to S3/Cloud Storage
3. Use Railway's built-in backup features

### Manual Backup

```bash
# Install Railway CLI
railway link

# Download outputs directory
railway run bash
# Then use scp or similar to download files
```

### Disaster Recovery

If deployment fails:

1. **Rollback to Previous Deployment**
   - Railway Dashboard → Deployments
   - Click previous working deployment
   - Click "Redeploy"

2. **Restore from Git**
   - Revert to last working commit
   - Push to GitHub
   - Railway auto-deploys

3. **Check Environment Variables**
   - Ensure all required vars are set
   - Verify API keys are valid

## Security Best Practices

### API Keys

✅ **DO:**
- Store all keys in Railway environment variables
- Rotate keys periodically
- Use separate keys for production/staging
- Monitor API usage for anomalies

❌ **DON'T:**
- Commit keys to git
- Share keys in logs or error messages
- Use same keys across environments

### Webhook Security

✅ **Enabled:**
- HMAC-SHA256 signature verification
- Secret-based authentication
- HTTPS only (Railway provides)

### Network Security

Railway provides:
- ✅ Automatic HTTPS/TLS
- ✅ DDoS protection
- ✅ Rate limiting (configurable)

## Production Checklist

Before going live with production traffic:

- [ ] All environment variables configured
- [ ] Tally webhook URL updated
- [ ] Slack bot configured and tested
- [ ] Test form submission successful
- [ ] Logs show no errors
- [ ] Slack notifications working
- [ ] PDF generation working
- [ ] Workflow status API working
- [ ] Health checks passing
- [ ] Custom domain configured (optional)
- [ ] Monitoring alerts set up
- [ ] Backup strategy in place

## Support & Resources

### Railway Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app

### Project Resources

- **Setup Guide:** `TALLY_WORKFLOW_README.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **API Documentation:** `/docs` endpoint

### Getting Help

1. **Check Railway Logs** - Most issues show up in logs
2. **Review Documentation** - Check this guide and Railway docs
3. **Railway Discord** - Active community support
4. **GitHub Issues** - Report bugs or request features

## Example: Complete Railway Deployment

Here's a complete example with Railway CLI:

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project (if not connected to GitHub)
railway init

# 4. Link to existing project (if already created via UI)
railway link

# 5. Set environment variables via CLI
railway variables set LLM_PROVIDER=openrouter
railway variables set LLM_MODEL=anthropic/claude-sonnet-4
railway variables set OPENROUTER_API_KEY=sk-or-v1-xxx
railway variables set VALYU_API_KEY=xxx
railway variables set TALLY_WEBHOOK_SECRET=whsec_xxx
railway variables set SLACK_BOT_TOKEN=xoxb-xxx
railway variables set SLACK_DEFAULT_CHANNEL=#marketing-research
railway variables set MAX_WEB_RESEARCH_LOOPS=10
railway variables set FETCH_FULL_PAGE=True
railway variables set INCLUDE_RAW_CONTENT=True

# 6. Deploy
railway up

# 7. View logs
railway logs --follow

# 8. Get deployment URL
railway domain

# 9. Test deployment
curl $(railway domain)

# 10. Open in browser
railway open
```

## Conclusion

Your market research automation system is now deployed on Railway! 🎉

The deployment includes:
- ✅ Automatic HTTPS
- ✅ Scalable infrastructure
- ✅ Built-in monitoring
- ✅ Easy environment management
- ✅ GitHub auto-deploy on push

Submit a Tally form to test the complete workflow from submission to PDF delivery via Slack.
