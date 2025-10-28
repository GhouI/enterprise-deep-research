# Tally Webhook Workflow Integration

This document describes the Tally form submission workflow that automatically generates market research reports and ad scripts.

## Overview

The workflow automates the following process:

1. **Tally Form Submission** → Brand submits intake form via Tally
2. **Webhook Reception** → FastAPI endpoint receives webhook
3. **Market Research** → Multi-agent system conducts deep research using ValyuSearchTool
4. **Script Generation** → Generates UGC and Podcast ad scripts
5. **PDF Generation** → Creates professional PDF report
6. **Slack Delivery** → Uploads PDF and sends notifications

## Architecture

```
┌─────────────┐
│ Tally Form  │
│ Submission  │
└──────┬──────┘
       │ Webhook
       ▼
┌──────────────────────────────────────┐
│ FastAPI: /api/tally/webhook          │
│ - Validates signature                │
│ - Returns 200 OK immediately         │
│ - Starts background workflow         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ TallyWorkflowService                 │
│ - Orchestrates entire workflow       │
└──────┬───────────────────────────────┘
       │
       ├─► Parse Submission
       │   └─► BrandIntakeData
       │
       ├─► Slack Start Notification
       │   └─► Post to channel
       │
       ├─► Market Research Phase
       │   ├─► Load marketPrompt.md
       │   ├─► Execute with agents
       │   ├─► Use ValyuSearchTool
       │   └─► Store results
       │
       ├─► Script Generation Phase
       │   ├─► Load scriptGenerator.md
       │   ├─► Use research data
       │   ├─► Generate scripts
       │   └─► Store scripts
       │
       ├─► PDF Generation
       │   └─► Create formatted report
       │
       └─► Slack Delivery
           ├─► Upload PDF
           └─► Completion notification
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `slack-sdk>=3.23.0` - For Slack notifications and file uploads
- `reportlab>=4.0.0` - For PDF generation

### 2. Configure Environment Variables

Copy `.env.sample` to `.env` and configure:

```bash
# Required: LLM Configuration (using OpenRouter)
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-sonnet-4
OPENROUTER_API_KEY=your_openrouter_key_here

# Required: Valyu API for web research
VALYU_API_KEY=your_valyu_key_here

# Required: Tally Webhook Secret
# Get this from your Tally form webhook settings
TALLY_WEBHOOK_SECRET=your_tally_secret_here

# Required: Slack Bot Token
# Create app at https://api.slack.com/apps
# Required scopes: chat:write, files:write, channels:read
SLACK_BOT_TOKEN=xoxb-your-slack-token

# Required: Slack Channel
SLACK_DEFAULT_CHANNEL=#marketing-research
```

### 3. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Marketing Research Bot"
4. Select your workspace

#### Configure OAuth Scopes:

Navigate to **OAuth & Permissions** and add these scopes:
- `chat:write` - Post messages
- `files:write` - Upload files
- `channels:read` - List channels

#### Install to Workspace:

1. Click "Install to Workspace"
2. Authorize the app
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
4. Add to `.env` as `SLACK_BOT_TOKEN`

### 4. Configure Tally Webhook

1. Open your Tally form
2. Go to **Integrations** → **Webhooks**
3. Add webhook URL: `https://your-domain.com/api/tally/webhook`
4. Copy the **Webhook Secret**
5. Add to `.env` as `TALLY_WEBHOOK_SECRET`

### 5. Start the Server

```bash
python app.py
```

Or with uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### POST /api/tally/webhook

Receives Tally form submissions and triggers workflow.

**Request Headers:**
- `X-Tally-Signature`: HMAC-SHA256 signature (automatically sent by Tally)

**Request Body:**
```json
{
  "event_id": "evt_123456",
  "event_type": "FORM_RESPONSE",
  "created_at": "2025-01-15T10:30:00Z",
  "data": {
    "fields": [
      {"key": "brand_name", "value": "Acme Corp"},
      {"key": "product_name", "value": "Magic Widget"},
      {"key": "product_description", "value": "..."},
      {"key": "target_audience", "value": "..."},
      ...
    ]
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "workflow_id": "uuid-here",
  "message": "Workflow started successfully",
  "status_url": "/api/tally/workflow/{workflow_id}/status"
}
```

### GET /api/tally/workflow/{workflow_id}/status

Check workflow execution status.

**Response:**
```json
{
  "workflow_id": "uuid-here",
  "status": "market_research",
  "current_step": "Conducting market research",
  "progress_percentage": 30,
  "result_url": null,
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "estimated_completion": null
}
```

**Status Values:**
- `pending` - Workflow initialized
- `parsing` - Parsing form submission
- `market_research` - Conducting market research
- `script_generation` - Generating ad scripts
- `pdf_generation` - Creating PDF report
- `completed` - Workflow completed successfully
- `failed` - Workflow failed with errors

### GET /api/tally/workflows

List recent workflow executions.

**Query Parameters:**
- `limit` (int, default: 20) - Maximum workflows to return
- `status` (string, optional) - Filter by status

**Response:**
```json
{
  "count": 5,
  "workflows": [
    {
      "workflow_id": "uuid-1",
      "brand_name": "Acme Corp",
      "product_name": "Magic Widget",
      "status": "completed",
      "created_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:45:00Z",
      "pdf_url": "https://files.slack.com/..."
    },
    ...
  ]
}
```

## Tally Form Field Mapping

The webhook endpoint expects these field keys in the Tally form:

| Tally Field Key | Required | Description |
|----------------|----------|-------------|
| `brand_name` or `brand` | Yes | Brand/company name |
| `product_name` or `product` | Yes | Product name |
| `product_description` or `description` | Yes | Detailed product description |
| `target_audience` or `audience` | Yes | Target customer profile |
| `unique_value_props` or `value_props` | Yes | Unique value propositions |
| `core_benefits` or `benefits` | Yes | Core product benefits |
| `website_url` or `website` | No | Brand website URL |
| `current_marketing` | No | Current marketing approach |
| `budget_constraints` | No | Budget and constraints |
| `competitors` | No | Known competitors |
| `additional_context` | No | Any additional context |

### Configuring Tally Form Fields

When creating your Tally form, use the **Question ID** feature to set the field keys:

1. Click on a question
2. Click the "⚙️" icon (Settings)
3. Set the **Question ID** to match the field keys above
4. Example: For brand name, set Question ID to `brand_name`

## Workflow Timing

Approximate duration for each phase:

- **Parsing**: < 1 second
- **Market Research**: 5-10 minutes (comprehensive research with ValyuSearchTool)
- **Script Generation**: 2-3 minutes (generates 15 UGC + 20 Podcast scripts)
- **PDF Generation**: 5-10 seconds
- **Slack Upload**: 2-5 seconds

**Total**: ~10-15 minutes end-to-end

## Slack Notifications

The workflow sends three types of Slack notifications:

### 1. Start Notification

Posted when workflow begins:

```
🚀 Market Research Workflow Started

Brand: Acme Corp
Product: Magic Widget
Workflow ID: uuid-here
Status: ⏳ In Progress

This workflow includes market research and script generation.
Estimated time: 10-15 minutes.
```

### 2. Progress Updates

Posted during execution:

```
🔍 Starting comprehensive market research...
✍️ Generating UGC and Podcast ad scripts...
📄 Generating PDF report...
```

### 3. Completion Notification

Posted when workflow finishes:

```
✅ Market Research Workflow Completed

Brand: Acme Corp
Product: Magic Widget
Workflow ID: uuid-here
Status: ✅ Completed

📄 Research Report & Scripts: [Download PDF]

The PDF contains comprehensive market research and generated ad scripts.
```

### 4. Error Notification (if failed)

Posted if workflow encounters errors:

```
❌ Market Research Workflow Failed

Brand: Acme Corp
Product: Magic Widget
Workflow ID: uuid-here
Status: ❌ Failed

Error: [error message]

Please check the logs for more details.
```

## PDF Report Structure

The generated PDF includes:

1. **Title Page**
   - Brand and product information
   - Workflow ID and timestamp

2. **Brand & Product Overview**
   - Product description
   - Target audience
   - Unique value propositions
   - Core benefits

3. **Market Research Findings**
   - Executive Summary
   - Brand Foundation & Positioning
   - Product Analysis & Differentiators
   - Market Landscape & Opportunity
   - Competitive Intelligence
   - Target Audience Insights
   - Customer Psychology & Pain Points
   - Objections & Purchase Barriers
   - Messaging Strategy & Frameworks
   - Strategic Recommendations

4. **Generated Ad Scripts**
   - **UGC Scripts** (15 scripts, 45-60 seconds each)
   - **Podcast Scripts** (20 scripts, 60-90 seconds each)

## File Storage

Generated files are stored in:

```
outputs/
├── pdfs/                    # Generated PDF reports
│   └── brandname_research_scripts_20250115_103045.pdf
└── workflows/               # Workflow state files (JSON)
    └── uuid.json
```

## Testing

### Run Unit Tests

```bash
pytest tests/test_tally_workflow.py -v
```

### Test Webhook Locally

Use the test endpoint to debug Tally payload structure:

```bash
curl -X POST http://localhost:8000/api/tally/test \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test_123",
    "event_type": "FORM_RESPONSE",
    "created_at": "2025-01-15T10:30:00Z",
    "data": {
      "fields": [
        {"key": "brand_name", "value": "Test Brand"},
        {"key": "product_name", "value": "Test Product"}
      ]
    }
  }'
```

### Test with ngrok (for Tally integration)

1. Install ngrok: https://ngrok.com/
2. Start your server locally
3. Run ngrok:
   ```bash
   ngrok http 8000
   ```
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. Configure in Tally: `https://abc123.ngrok.io/api/tally/webhook`
6. Submit test form

## Monitoring

### Check Workflow Status

```bash
curl http://localhost:8000/api/tally/workflow/{workflow_id}/status
```

### List Recent Workflows

```bash
curl http://localhost:8000/api/tally/workflows?limit=10
```

### View Logs

Logs are written to:
- Console (stdout)
- `backend_logs.txt`

Key log patterns to search for:
- `[{workflow_id}]` - All logs for specific workflow
- `Step 1:`, `Step 2:`, etc. - Workflow progress
- `ERROR` - Error messages

## Troubleshooting

### Webhook not receiving requests

1. **Check Tally webhook configuration**
   - Verify URL is correct
   - Ensure webhook is enabled
   - Check webhook logs in Tally dashboard

2. **Check server logs**
   ```bash
   tail -f backend_logs.txt | grep "Tally webhook"
   ```

3. **Test with curl**
   ```bash
   curl -X POST http://your-domain.com/api/tally/test \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Slack notifications not sending

1. **Check token**
   ```bash
   echo $SLACK_BOT_TOKEN
   ```

2. **Verify scopes**
   - Go to https://api.slack.com/apps
   - Check OAuth scopes are correct

3. **Test channel access**
   - Ensure bot is added to the channel
   - Use `/invite @bot-name` in Slack channel

### PDF generation failing

1. **Check ReportLab installation**
   ```bash
   python -c "import reportlab; print(reportlab.Version)"
   ```

2. **Check output directory permissions**
   ```bash
   ls -la outputs/pdfs/
   ```

3. **Review logs for specific error**
   ```bash
   grep "Error generating PDF" backend_logs.txt
   ```

### Workflow timing out

1. **Check LLM API limits**
   - OpenRouter rate limits
   - API key credits

2. **Monitor research loops**
   - Check `MAX_WEB_RESEARCH_LOOPS` in .env
   - Reduce if hitting timeouts

3. **Review Valyu API status**
   - Check API key is valid
   - Verify no rate limiting

## Security Considerations

### Webhook Signature Verification

The endpoint verifies Tally webhook signatures using HMAC-SHA256:

```python
def verify_tally_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

Always set `TALLY_WEBHOOK_SECRET` in production to prevent unauthorized webhook calls.

### API Key Protection

Never commit API keys to git:
- Use `.env` file (already in `.gitignore`)
- Use environment variables in production
- Rotate keys periodically

### Slack Token Security

The Slack bot token has full access to post messages and upload files:
- Use workspace-scoped token (not user token)
- Limit scopes to minimum required
- Store securely in environment variables

## Production Deployment

### Environment Setup

For production deployment:

1. **Use process manager** (e.g., systemd, supervisor, PM2)
2. **Configure reverse proxy** (nginx, Apache)
3. **Enable HTTPS** (Let's Encrypt)
4. **Set proper environment variables**
5. **Configure log rotation**

### Example systemd Service

```ini
[Unit]
Description=Market Research Workflow API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/market-research-api
Environment="PATH=/var/www/market-research-api/venv/bin"
EnvironmentFile=/var/www/market-research-api/.env
ExecStart=/var/www/market-research-api/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Example nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /api/tally/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Support

For issues or questions:

1. Check logs in `backend_logs.txt`
2. Review workflow status via API
3. Check Slack channel for notifications
4. Review this documentation

## Version History

- **v1.0.0** (2025-01-15): Initial implementation
  - Tally webhook integration
  - Market research workflow
  - Script generation
  - PDF generation
  - Slack notifications
