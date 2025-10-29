# Quickstart Guide

Get up and running with Invoices-Agent in 10 minutes!

## Prerequisites

- Python 3.9+
- Azure account (for Microsoft Graph API)
- OpenAI API key
- Outlook/Microsoft 365 account

## Step 1: Azure App Registration (5 minutes)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Enter app name: "Invoices-Agent"
4. Select **Accounts in this organizational directory only**
5. Click **Register**

6. **Note down** the following from the Overview page:
   - Application (client) ID
   - Directory (tenant) ID

7. Go to **Certificates & secrets** → **New client secret**
   - Description: "Invoices-Agent Secret"
   - Expires: 24 months
   - Click **Add**
   - **Copy the secret value immediately** (you can't see it again!)

8. Go to **API permissions** → **Add a permission**
   - Select **Microsoft Graph** → **Application permissions**
   - Add these permissions:
     - `Mail.Read`
     - `Mail.ReadWrite`
   - Click **Add permissions**
   - Click **Grant admin consent** (requires admin)

## Step 2: Get OpenAI API Key (2 minutes)

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create account
3. Go to **API keys** → **Create new secret key**
4. Copy the key and save it securely

## Step 3: Install Invoices-Agent (3 minutes)

### Option A: Using run.sh (Recommended)

```bash
# Clone the repository
git clone https://github.com/jyntreddy/Invoices-Agent.git
cd Invoices-Agent

# Make run script executable
chmod +x run.sh

# Run the script (it will set everything up)
./run.sh
```

The script will:
- Create virtual environment
- Install dependencies
- Prompt you to configure `.env` file

### Option B: Manual Setup

```bash
# Clone the repository
git clone https://github.com/jyntreddy/Invoices-Agent.git
cd Invoices-Agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
```

## Step 4: Configure Environment Variables

Edit `.env` file with your credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_MODEL=gpt-4

# Microsoft Graph API Configuration
AZURE_CLIENT_ID=your-client-id-from-step-1
AZURE_CLIENT_SECRET=your-secret-from-step-1
AZURE_TENANT_ID=your-tenant-id-from-step-1
USER_EMAIL=your-email@company.com

# Keep other settings as default for now
```

## Step 5: Start the Server

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 6: Test It Out!

### Test 1: Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T...",
  "service": "Invoices-Agent MCP Server"
}
```

### Test 2: Check Emails

```bash
curl -X POST http://localhost:8000/api/v1/check-emails \
  -H "Content-Type: application/json" \
  -d '{"max_emails": 5, "unread_only": true}'
```

This will:
1. Fetch your latest 5 unread emails
2. Download any attachments
3. Classify each attachment as invoice/non-invoice
4. Move files to appropriate folders
5. Return the results

### Test 3: View Results

Check your storage folders:
```bash
ls storage/invoices/
ls storage/others/
```

### Test 4: Get Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

Response:
```json
{
  "invoices": 3,
  "others": 2,
  "temp": 0,
  "total_processed": 5,
  "timestamp": "2025-10-29T..."
}
```

## Step 7: Interactive API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can test all endpoints interactively!

## Common Issues & Solutions

### Issue: "No module named 'app'"

**Solution**: Make sure you're in the project root directory and virtual environment is activated:
```bash
cd Invoices-Agent
source venv/bin/activate
```

### Issue: "ValidationError" when starting server

**Solution**: Check your `.env` file has all required values:
```bash
grep -E "^[A-Z]" .env
```

### Issue: "Authentication failed" when checking emails

**Solution**: 
1. Verify your Azure credentials in `.env`
2. Ensure admin consent was granted in Azure portal
3. Check USER_EMAIL matches your Outlook account

### Issue: "File not found" errors

**Solution**: Ensure storage directories exist:
```bash
mkdir -p storage/invoices storage/others storage/temp logs
```

## Next Steps

### 1. Automate with Scheduler

Use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Add to crontab (run every 5 minutes)
*/5 * * * * curl -X POST http://localhost:8000/api/v1/check-emails \
  -H "Content-Type: application/json" \
  -d '{"max_emails": 10, "unread_only": true}'
```

### 2. Integrate with n8n

1. Import the workflow: `examples/n8n_workflow.json`
2. Configure HTTP Request node with your server URL
3. Set schedule trigger (e.g., every 5 minutes)

### 3. Deploy to Production

See [Docker deployment](#docker-deployment) or deploy to:
- AWS (EC2, ECS, Lambda)
- Azure (App Service, Container Instances)
- Google Cloud (Cloud Run, Compute Engine)
- DigitalOcean (Droplets, App Platform)

### 4. Customize Classification

Edit `app/services/classifier_service.py` to:
- Add custom document types
- Adjust classification prompts
- Extract specific metadata fields

## Docker Deployment

### Quick Docker Run

```bash
# Build image
docker build -t invoices-agent .

# Run container
docker run -d \
  --name invoices-agent \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/logs:/app/logs \
  invoices-agent
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Security**: See [SECURITY.md](SECURITY.md)
- **Issues**: [GitHub Issues](https://github.com/jyntreddy/Invoices-Agent/issues)
- **API Docs**: http://localhost:8000/docs

## Pro Tips

1. **Start Small**: Process 1-2 emails first to test
2. **Monitor Logs**: Use `tail -f logs/app.log` to watch activity
3. **Test Classification**: Upload a sample invoice manually first
4. **Backup Storage**: Keep backups of classified documents
5. **Rate Limits**: Be mindful of OpenAI API rate limits

---

**Congratulations!** 🎉 You now have a fully functional AI-powered invoice classifier running!
