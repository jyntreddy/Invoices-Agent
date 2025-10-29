"""Agent workflow using LangGraph for orchestrating the email processing pipeline."""

from typing import TypedDict, Annotated, Sequence
from datetime import datetime
from pathlib import Path

from langgraph.graph import Graph, StateGraph, END
from langchain_core.messages import BaseMessage

from app.models import (
    EmailMessage,
    Attachment,
    ProcessingResult,
    ClassificationResult,
    DocumentType,
)
from app.services.email_service import EmailService
from app.services.classifier_service import ClassifierService
from app.services.storage_service import StorageService
from app.utils.logger import get_logger

logger = get_logger()


class AgentState(TypedDict):
    """State for the agent workflow."""
    email: EmailMessage
    attachment: Attachment
    temp_file_path: str
    classification: ClassificationResult
    destination_path: str
    error: str
    success: bool


class AgentWorkflow:
    """
    LangGraph-based workflow for processing email attachments.
    
    Workflow steps:
    1. Download attachment
    2. Classify document
    3. Move to destination
    4. Cleanup
    """

    def __init__(self):
        """Initialize workflow with required services."""
        self.email_service = EmailService()
        self.classifier_service = ClassifierService()
        self.storage_service = StorageService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        
        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("download", self._download_attachment)
        workflow.add_node("classify", self._classify_document)
        workflow.add_node("move_file", self._move_to_destination)
        workflow.add_node("cleanup", self._cleanup)
        workflow.add_node("handle_error", self._handle_error)

        # Set entry point
        workflow.set_entry_point("download")

        # Add edges
        workflow.add_conditional_edges(
            "download",
            self._check_download_success,
            {
                "success": "classify",
                "error": "handle_error",
            }
        )

        workflow.add_conditional_edges(
            "classify",
            self._check_classification_success,
            {
                "success": "move_file",
                "error": "handle_error",
            }
        )

        workflow.add_conditional_edges(
            "move_file",
            self._check_move_success,
            {
                "success": "cleanup",
                "error": "handle_error",
            }
        )

        workflow.add_edge("cleanup", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def _download_attachment(self, state: AgentState) -> AgentState:
        """Download attachment to temporary storage."""
        try:
            logger.info(f"Downloading attachment: {state['attachment'].name}")
            
            temp_path = self.storage_service.get_temp_path(state['attachment'].name)
            
            file_path = await self.email_service.download_attachment(
                email_id=state['email'].id,
                attachment_id=state['attachment'].attachment_id,
                save_path=temp_path,
            )
            
            state['temp_file_path'] = file_path
            state['success'] = True
            logger.info(f"Download successful: {file_path}")
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            state['error'] = f"Download failed: {str(e)}"
            state['success'] = False
            
        return state

    async def _classify_document(self, state: AgentState) -> AgentState:
        """Classify the document using AI."""
        try:
            logger.info(f"Classifying document: {state['temp_file_path']}")
            
            classification = await self.classifier_service.classify_document(
                state['temp_file_path']
            )
            
            state['classification'] = classification
            state['success'] = True
            logger.info(
                f"Classification complete: {classification.document_type} "
                f"(confidence: {classification.confidence:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state['error'] = f"Classification failed: {str(e)}"
            state['success'] = False
            
        return state

    async def _move_to_destination(self, state: AgentState) -> AgentState:
        """Move file to appropriate destination folder."""
        try:
            logger.info(f"Moving file based on classification: {state['classification'].document_type}")
            
            source_path = Path(state['temp_file_path'])
            dest_path = self.storage_service.move_to_destination(
                source_path=source_path,
                document_type=state['classification'].document_type,
            )
            
            state['destination_path'] = dest_path
            state['success'] = True
            logger.info(f"File moved to: {dest_path}")
            
        except Exception as e:
            logger.error(f"Move failed: {e}")
            state['error'] = f"Move failed: {str(e)}"
            state['success'] = False
            
        return state

    async def _cleanup(self, state: AgentState) -> AgentState:
        """Cleanup any temporary resources."""
        try:
            logger.info("Workflow completed successfully")
            # Cleanup temp files older than 1 hour
            self.storage_service.cleanup_temp_files(older_than_seconds=3600)
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
            
        return state

    async def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow."""
        logger.error(f"Workflow error: {state.get('error', 'Unknown error')}")
        
        # Cleanup temp file if it exists
        if 'temp_file_path' in state and state['temp_file_path']:
            try:
                temp_path = Path(state['temp_file_path'])
                if temp_path.exists():
                    temp_path.unlink()
                    logger.info(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
                
        return state

    def _check_download_success(self, state: AgentState) -> str:
        """Check if download was successful."""
        return "success" if state.get('success', False) else "error"

    def _check_classification_success(self, state: AgentState) -> str:
        """Check if classification was successful."""
        return "success" if state.get('success', False) else "error"

    def _check_move_success(self, state: AgentState) -> str:
        """Check if move was successful."""
        return "success" if state.get('success', False) else "error"

    async def process_attachment(
        self, email: EmailMessage, attachment: Attachment
    ) -> ProcessingResult:
        """
        Process a single email attachment through the workflow.

        Args:
            email: Email message containing the attachment
            attachment: Attachment to process

        Returns:
            ProcessingResult with processing details
        """
        logger.info(f"Starting workflow for attachment: {attachment.name}")
        
        # Initialize state
        initial_state: AgentState = {
            'email': email,
            'attachment': attachment,
            'temp_file_path': '',
            'classification': None,
            'destination_path': '',
            'error': '',
            'success': False,
        }

        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Build result
            if final_state.get('success', False) and final_state.get('classification'):
                result = ProcessingResult(
                    attachment_name=attachment.name,
                    classification=final_state['classification'],
                    destination_path=final_state.get('destination_path', ''),
                    processed_at=datetime.now(),
                    success=True,
                    error_message=None,
                )
            else:
                result = ProcessingResult(
                    attachment_name=attachment.name,
                    classification=ClassificationResult(
                        document_type=DocumentType.UNKNOWN,
                        confidence=0.0,
                        reasoning="Processing failed",
                        metadata={}
                    ),
                    destination_path='',
                    processed_at=datetime.now(),
                    success=False,
                    error_message=final_state.get('error', 'Unknown error'),
                )
                
            logger.info(f"Workflow completed for {attachment.name}: success={result.success}")
            return result

        except Exception as e:
            logger.error(f"Workflow exception: {e}")
            return ProcessingResult(
                attachment_name=attachment.name,
                classification=ClassificationResult(
                    document_type=DocumentType.UNKNOWN,
                    confidence=0.0,
                    reasoning="Workflow exception",
                    metadata={}
                ),
                destination_path='',
                processed_at=datetime.now(),
                success=False,
                error_message=str(e),
            )
