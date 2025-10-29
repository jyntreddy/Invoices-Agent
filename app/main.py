"""Main FastAPI application for the Invoices-Agent MCP server."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import get_settings
from app.utils.logger import setup_logger, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger = setup_logger()
    logger.info("Starting Invoices-Agent MCP Server")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Storage Path: {settings.storage_base_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Invoices-Agent MCP Server")


# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Invoices-Agent MCP Server",
    description=(
        "AI-powered email invoice classifier using LangChain, LangGraph, and FastAPI. "
        "Monitors Outlook emails, extracts attachments, and classifies documents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["Invoices Agent"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Invoices-Agent MCP Server",
        "version": "1.0.0",
        "description": "AI-powered email invoice classifier",
        "endpoints": {
            "health": "/api/v1/health",
            "check_emails": "/api/v1/check-emails",
            "classify": "/api/v1/classify",
            "upload": "/api/v1/upload-and-classify",
            "stats": "/api/v1/stats",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
