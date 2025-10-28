# Railway Quick Start Checklist ✅

Follow this checklist to deploy in under 15 minutes.

## Prerequisites

Gather these before starting:

- [ ] OpenRouter API Key - Get from https://openrouter.ai/keys
- [ ] Valyu API Key - Get from https://valyu.com
- [ ] Slack Bot Token - Create app at https://api.slack.com/apps
- [ ] Tally Form - Create at https://tally.so
- [ ] GitHub account
- [ ] Railway account - Sign up at https://railway.app

---

## Step 1: Prepare Repository (2 minutes)

- [ ] Clone/download this repository
- [ ] Verify these files exist:
  ```
  ✅ Dockerfile
  ✅ .dockerignore
  ✅ railway.json
  ✅ requirements.txt
  ```
- [ ] Push to your GitHub repository

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

## Step 2: Create Slack App (3 minutes)

- [ ] Go to https://api.slack.com/apps
- [ ] Click **"Create New App"** → **"From scratch"**
- [ ] Name: "Marketing Research Bot"
- [ ] Select your workspace
- [ ] Go to **"OAuth & Permissions"**
- [ ] Add Bot Token Scopes:
  - [ ] `chat:write`
  - [ ] `files:write`
  - [ ] `channels:read`
- [ ] Click **"Install to Workspace"**
- [ ] Copy **Bot User OAuth Token** (starts with `xoxb-`)
- [ ] Invite bot to your channel: `/invite @Marketing Research Bot`

---

## Step 3: Deploy to Railway (3 minutes)

- [ ] Go to https://railway.app
- [ ] Click **"New Project"**
- [ ] Select **"Deploy from GitHub repo"**
- [ ] Select repository: `enterpirse-deepsearch`
- [ ] Railway auto-detects Dockerfile and starts building
- [ ] Wait for build to complete (~3-5 minutes)
- [ ] Copy your Railway URL (e.g., `https://enterpirse-deepsearch-production.up.railway.app`)

---

## Step 4: Configure Environment Variables (5 minutes)

In Railway Dashboard → **Variables** tab, add these:

### LLM & Research (Required)

```
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-sonnet-4
OPENROUTER_API_KEY=your_key_here
VALYU_API_KEY=your_key_here
MAX_WEB_RESEARCH_LOOPS=10
FETCH_FULL_PAGE=True
INCLUDE_RAW_CONTENT=True
```

### Activity Generation (Required)

```
ENABLE_ACTIVITY_GENERATION=true
ACTIVITY_VERBOSITY=medium
ACTIVITY_LLM_PROVIDER=openrouter
ACTIVITY_LLM_MODEL=anthropic/claude-sonnet-4
```

### Slack (Required)

```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_DEFAULT_CHANNEL=#marketing-research
```

### Tally (Will add in Step 6)

```
TALLY_WEBHOOK_SECRET=will_add_after_tally_setup
```

- [ ] Click **"Redeploy"** after adding variables

---

## Step 5: Verify Deployment (1 minute)

Test your deployment:

```bash
# Replace with your Railway URL
curl https://your-app.railway.app/

# Should return:
# {"message": "Deep Research API is running", ...}
```

- [ ] API responds successfully
- [ ] Check Railway logs (no errors)

---

## Step 6: Configure Tally Webhook (2 minutes)

- [ ] Open your Tally form
- [ ] Go to **Integrations** → **Webhooks**
- [ ] Click **"Add Webhook"**
- [ ] Enter URL: `https://your-app.railway.app/api/tally/webhook`
- [ ] Copy the **Webhook Secret** (starts with `whsec_`)
- [ ] Go back to Railway → **Variables**
- [ ] Add: `TALLY_WEBHOOK_SECRET=whsec_your_secret_here`
- [ ] Click **"Redeploy"**

---

## Step 7: Test Complete Workflow (1 minute)

- [ ] Submit a test via your Tally form
- [ ] Check Railway logs for:
  ```
  Received Tally webhook: event_type=FORM_RESPONSE
  ```
- [ ] Check Slack for start notification:
  ```
  🚀 Market Research Workflow Started
  ```
- [ ] Wait 10-15 minutes
- [ ] Check Slack for completion and PDF:
  ```
  ✅ Market Research Workflow Completed
  📄 Research Report & Scripts: [Download PDF]
  ```

---

## ✅ Deployment Complete!

Your system is now live and ready to process Tally form submissions automatically!

### What Happens Now?

1. **User submits Tally form** → Brand intake data captured
2. **Webhook triggers** → Railway receives submission
3. **Market research** → AI agents conduct deep research (5-10 min)
4. **Script generation** → Creates UGC and Podcast ads (2-3 min)
5. **PDF creation** → Formats professional report (10 sec)
6. **Slack delivery** → Uploads PDF to your channel

### Quick Links

- **Your Railway App:** https://railway.app/project/[your-project]
- **API Documentation:** https://your-app.railway.app/docs
- **Check Workflows:** https://your-app.railway.app/api/tally/workflows
- **View Logs:** Railway Dashboard → Deployments → Logs

### Need Help?

- 📖 **Full Guide:** See `RAILWAY_DEPLOYMENT.md`
- 🔍 **Troubleshooting:** Check Railway logs first
- 💬 **Railway Discord:** https://discord.gg/railway
- 📚 **Documentation:** See `TALLY_WORKFLOW_README.md`

---

## Optional: Custom Domain

Want to use your own domain?

1. Railway Dashboard → **Settings** → **Domains**
2. Click **"Add Custom Domain"**
3. Enter: `api.yourdomain.com`
4. Add CNAME record to your DNS:
   ```
   Type: CNAME
   Name: api
   Value: your-app.railway.app
   ```
5. Wait for DNS propagation (5-30 min)
6. Update Tally webhook URL

---

## Cost Estimate

**Railway Starter Plan:** $5/month

**Usage estimate (50 workflows/month):**
- Compute: ~2-3 hours
- Memory: 1-2 GB average
- Storage: ~250 MB
- Network: ~5 GB

**Total cost:** ~$5-10/month for moderate usage

---

## Troubleshooting Quick Fixes

### Build Failed
```bash
# Check Dockerfile syntax
docker build -t test .
```

### Webhook Not Working
```bash
# Test endpoint
curl -X POST https://your-app.railway.app/api/tally/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Slack Not Posting
- [ ] Verify SLACK_BOT_TOKEN is correct
- [ ] Check bot is in channel: `/invite @bot`
- [ ] Check Railway logs for Slack errors

### PDF Generation Failed
- [ ] Check Railway logs for ReportLab errors
- [ ] Verify memory limit (increase if needed)

---

**Congratulations! 🎉 Your market research automation is live!**
