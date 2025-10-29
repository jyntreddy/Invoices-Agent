# Invoices-Agent 

An intelligent agentic AI backend that monitors Outlook emails, extracts attachments, classifies documents as invoices or non-invoices using AI, and automatically organizes files into appropriate folders.

## Tech Stack

- **LangChain** → LLM orchestration and document classification
- **LangGraph** → Agent workflow with branching and decision logic
- **FastAPI** → MCP (Model Context Protocol) server for external integrations
- **Microsoft Graph API** → Outlook email monitoring and attachment extraction
- **OpenAI GPT-4** → Document classification (supports other LLMs)
- **Python 3.9+** → Core programming language

## Architecture

```
┌─────────────────┐
│  Outlook Email  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Email Service  │ ← Microsoft Graph API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Workflow  │ ← LangGraph Orchestration
│   (LangGraph)   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────┐   ┌──────────┐
│Down-│   │Classify  │ ← LangChain + OpenAI
│load │   │Document  │
└──┬──┘   └────┬─────┘
   │           │
   └─────┬─────┘
         ▼
   ┌──────────┐
   │Move File │
   └─────┬────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────┐
│/invoices│ │/others│
└─────────┘ └──────┘
```

## ✨ Features

- 📨 **Automated Email Monitoring**: Fetches emails from Outlook via Microsoft Graph API
- 📎 **Attachment Extraction**: Downloads email attachments automatically
- 🧠 **AI Classification**: Uses GPT-4 to classify documents as invoices or non-invoices
- 📁 **Smart Organization**: Automatically moves files to `/invoices/` or `/others/` folders
- 🔄 **Workflow Orchestration**: LangGraph manages the entire processing pipeline
- 🌐 **RESTful API**: FastAPI endpoints for external integrations (n8n, webhooks, etc.)
- 📊 **Statistics & Monitoring**: Track processing stats and document counts
- 🔒 **Secure**: Azure AD authentication for Microsoft Graph API

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure App Registration (for Microsoft Graph API)
- OpenAI API key
- Outlook/Microsoft 365 account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jyntreddy/Invoices-Agent.git
cd Invoices-Agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.template .env
# Edit .env with your credentials
```

5. **Set up Azure App Registration**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new App Registration
   - Add API permissions: `Mail.Read`, `Mail.ReadWrite`
   - Create a client secret
   - Add credentials to `.env`

### Configuration

Edit `.env` file with your credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Microsoft Graph API Configuration
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id
USER_EMAIL=your_outlook_email@example.com

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Storage Configuration
STORAGE_BASE_PATH=./storage
INVOICES_FOLDER=invoices
OTHERS_FOLDER=others
TEMP_FOLDER=temp

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Email Monitoring
EMAIL_CHECK_INTERVAL=300
MAX_EMAILS_PER_CHECK=10
```

### Running the Server

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python app/main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Check Emails
Process emails and attachments from Outlook:
```bash
POST /api/v1/check-emails
Content-Type: application/json

{
  "max_emails": 10,
  "unread_only": true
}
```

### Classify Document
Classify an existing document:
```bash
POST /api/v1/classify
Content-Type: application/json

{
  "file_path": "/path/to/document.pdf",
  "file_name": "document.pdf"
}
```

### Upload and Classify
Upload a file for classification:
```bash
POST /api/v1/upload-and-classify
Content-Type: multipart/form-data

file: <binary file data>
```

### Get Statistics
Get processing statistics:
```bash
GET /api/v1/stats
```

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Usage Examples

### Using cURL

```bash
# Check emails
curl -X POST http://localhost:8000/api/v1/check-emails \
  -H "Content-Type: application/json" \
  -d '{"max_emails": 5, "unread_only": true}'

# Upload and classify
curl -X POST http://localhost:8000/api/v1/upload-and-classify \
  -F "file=@/path/to/invoice.pdf"

# Get stats
curl http://localhost:8000/api/v1/stats
```

### Using Python

```python
import requests

# Check emails
response = requests.post(
    "http://localhost:8000/api/v1/check-emails",
    json={"max_emails": 10, "unread_only": True}
)
print(response.json())

# Upload and classify
with open("invoice.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload-and-classify",
        files={"file": f}
    )
print(response.json())
```

### Integration with n8n

1. Create an HTTP Request node
2. Set method to POST
3. Set URL to `http://your-server:8000/api/v1/check-emails`
4. Add JSON body:
```json
{
  "max_emails": 10,
  "unread_only": true
}
```
5. Schedule with a Cron node for automated processing

## 📁 Project Structure

```
Invoices-Agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_workflow.py   # LangGraph workflow
│   │   ├── classifier_service.py # LangChain classifier
│   │   ├── email_service.py    # Microsoft Graph API
│   │   └── storage_service.py  # File management
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging configuration
│       └── document_processor.py # Text extraction
├── storage/
│   ├── invoices/              # Classified invoices
│   ├── others/                # Non-invoice documents
│   └── temp/                  # Temporary storage
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
├── .env.template             # Environment template
├── .gitignore
└── README.md
```

## 🔄 Workflow Process

1. **Email Monitoring**: FastAPI endpoint triggers email check
2. **Fetch Emails**: Microsoft Graph API retrieves recent emails
3. **Download Attachments**: Extracts and saves attachments to temp folder
4. **LangGraph Workflow Execution**:
   - **Node 1**: Download attachment
   - **Node 2**: Extract text from document
   - **Node 3**: Classify using LangChain + GPT-4
   - **Node 4**: Move to appropriate folder based on classification
   - **Node 5**: Cleanup temporary files
5. **Mark as Read**: Updates email status in Outlook
6. **Return Results**: API returns processing results

## 🎯 Classification Logic

The classifier uses GPT-4 to analyze documents based on:

- Invoice number or ID
- Date of issuance
- Seller/vendor information
- Buyer/customer information
- Line items with prices
- Subtotal, taxes, and total amount
- Payment terms

The model returns:
- **Document Type**: `invoice` or `non_invoice`
- **Confidence Score**: 0.0 to 1.0
- **Reasoning**: Explanation of classification
- **Metadata**: Extracted information (invoice number, date, total, etc.)

## 🔐 Security Considerations

- Store API keys in environment variables, never in code
- Use Azure AD authentication for Microsoft Graph API
- Implement rate limiting for production deployments
- Configure CORS appropriately for your use case
- Use HTTPS in production
- Regularly rotate API keys and secrets

## 🧪 Testing

```bash
# Run the server
python app/main.py

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test with sample document
curl -X POST http://localhost:8000/api/v1/upload-and-classify \
  -F "file=@sample_invoice.pdf"
```

## 📊 Monitoring

Application logs are stored in `./logs/app.log` with:
- Rotation at 10 MB
- Retention for 30 days
- Automatic compression

View logs:
```bash
tail -f logs/app.log
```

## 🚧 Future Enhancements

- [ ] Support for additional document types (receipts, quotes, purchase orders)
- [ ] Multi-language support
- [ ] Database integration for tracking processing history
- [ ] Email notification on classification
- [ ] Batch processing optimization
- [ ] Support for other email providers (Gmail, etc.)
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
- [ ] Web UI dashboard
- [ ] Advanced filtering and search

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🙋 Support

For issues, questions, or suggestions, please open an issue on GitHub.

## 🔗 Related Technologies

- [LangChain](https://langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [OpenAI](https://openai.com/)

---

Built with ❤️ using LangChain, LangGraph, and FastAPI
