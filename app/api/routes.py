"""FastAPI routes for the MCP server."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path

from app.models import (
    EmailCheckRequest,
    EmailCheckResponse,
    ClassifyRequest,
    ClassifyResponse,
    ProcessingResult,
)
from app.services import EmailService, ClassifierService, StorageService, AgentWorkflow
from app.utils.logger import get_logger
from app.utils.security import is_safe_path, sanitize_filename
from app.config import get_settings

logger = get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Invoices-Agent MCP Server"
    }


@router.post("/check-emails", response_model=EmailCheckResponse)
async def check_emails(request: EmailCheckRequest):
    """
    Check Outlook emails and process attachments.
    
    This endpoint:
    1. Fetches recent emails from Outlook
    2. Downloads attachments
    3. Classifies each attachment as invoice/non-invoice
    4. Moves files to appropriate folders
    """
    try:
        logger.info(f"Email check requested: max_emails={request.max_emails}, unread_only={request.unread_only}")
        
        # Initialize services
        email_service = EmailService()
        workflow = AgentWorkflow()
        
        # Fetch emails
        emails = await email_service.get_recent_emails(
            max_count=request.max_emails,
            unread_only=request.unread_only
        )
        
        logger.info(f"Found {len(emails)} emails to process")
        
        results: List[ProcessingResult] = []
        
        # Process each email's attachments
        for email in emails:
            if not email.has_attachments or not email.attachments:
                logger.info(f"Email {email.id} has no attachments, skipping")
                continue
                
            logger.info(f"Processing email: {email.subject} ({len(email.attachments)} attachments)")
            
            for attachment in email.attachments:
                # Process through workflow
                result = await workflow.process_attachment(email, attachment)
                results.append(result)
            
            # Mark email as read after processing
            try:
                await email_service.mark_as_read(email.id)
            except Exception as e:
                logger.warning(f"Failed to mark email as read: {e}")
        
        response = EmailCheckResponse(
            emails_processed=len(emails),
            attachments_processed=len(results),
            results=results,
            timestamp=datetime.now()
        )
        
        logger.info(f"Email check complete: {response.attachments_processed} attachments processed")
        return response
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest):
    """
    Classify a single document.
    
    This endpoint classifies an existing file without processing emails.
    """
    try:
        logger.info(f"Classification requested for: {request.file_path}")
        
        # Validate path for security
        settings = get_settings()
        storage_base = str(settings.storage_base_path)
        
        if not is_safe_path(request.file_path, base_dir=storage_base):
            logger.warning(f"Unsafe path detected: {request.file_path}")
            raise HTTPException(status_code=400, detail="Invalid or unsafe file path")
        
        # Check if file exists
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Initialize classifier
        classifier = ClassifierService()
        
        # Classify document
        classification = await classifier.classify_document(str(file_path))
        
        response = ClassifyResponse(
            file_name=request.file_name or file_path.name,
            classification=classification,
            timestamp=datetime.now()
        )
        
        logger.info(f"Classification complete: {classification.document_type}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-and-classify", response_model=ClassifyResponse)
async def upload_and_classify(file: UploadFile = File(...)):
    """
    Upload a file and classify it.
    
    This endpoint allows uploading a file directly for classification.
    """
    try:
        logger.info(f"File upload and classification requested: {file.filename}")
        
        # Sanitize filename to prevent path traversal
        safe_filename = sanitize_filename(file.filename)
        logger.info(f"Sanitized filename: {safe_filename}")
        
        # Initialize services
        storage_service = StorageService()
        classifier = ClassifierService()
        
        # Save uploaded file to temp storage
        temp_path = storage_service.get_temp_path(safe_filename)
        
        # SECURITY: Limit file size to prevent DoS (50MB max)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        file_size = 0
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            file_size = len(content)
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 50MB")
            
            f.write(content)
        
        logger.info(f"File saved to temp: {temp_path} (size: {file_size} bytes)")
        
        # Classify
        classification = await classifier.classify_document(str(temp_path))
        
        # Move to destination
        final_path = storage_service.move_to_destination(
            source_path=temp_path,
            document_type=classification.document_type,
        )
        
        response = ClassifyResponse(
            file_name=safe_filename,
            classification=classification,
            timestamp=datetime.now()
        )
        
        logger.info(f"Upload and classification complete: {classification.document_type}, saved to {final_path}")
        return response
        
    except Exception as e:
        logger.error(f"Error in upload and classify: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get statistics about processed documents."""
    try:
        from app.config import get_settings
        settings = get_settings()
        
        # Count files in each folder
        invoices_count = len(list(settings.invoices_path.glob("*"))) - 1  # Exclude .gitkeep
        others_count = len(list(settings.others_path.glob("*"))) - 1
        temp_count = len(list(settings.temp_path.glob("*"))) - 1
        
        return {
            "invoices": max(0, invoices_count),
            "others": max(0, others_count),
            "temp": max(0, temp_count),
            "total_processed": max(0, invoices_count + others_count),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
