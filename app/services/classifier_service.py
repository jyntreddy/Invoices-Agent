"""Classifier service using LangChain for document classification."""

import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from app.config import get_settings
from app.models import ClassificationResult, DocumentType
from app.utils.logger import get_logger
from app.utils.document_processor import extract_text_from_file

logger = get_logger()


class ClassifierService:
    """Service for classifying documents using LLM."""

    def __init__(self):
        """Initialize classifier with LangChain components."""
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            openai_api_key=self.settings.openai_api_key,
            temperature=0,
        )
        self._setup_chain()

    def _setup_chain(self):
        """Set up the LangChain prompt and chain."""
        # Classification prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert document classifier specialized in identifying invoices.

Your task is to analyze the provided document text and determine if it is an invoice or not.

An invoice typically contains:
- Invoice number or ID
- Date of issuance
- Seller/vendor information (name, address, contact)
- Buyer/customer information
- Line items with descriptions and prices
- Subtotal, taxes, and total amount
- Payment terms or due date

Respond with a JSON object containing:
- document_type: "invoice" or "non_invoice"
- confidence: a float between 0.0 and 1.0
- reasoning: a brief explanation of your classification
- metadata: any relevant extracted information (invoice_number, date, total_amount, etc.)

Be thorough but concise in your reasoning."""),
            ("user", """Please classify the following document:

Filename: {filename}

Document Text:
{document_text}

Provide your classification in JSON format.""")
        ])

    async def classify_document(self, file_path: str) -> ClassificationResult:
        """
        Classify a document as invoice or non-invoice.

        Args:
            file_path: Path to the document file

        Returns:
            ClassificationResult with classification details
        """
        try:
            logger.info(f"Classifying document: {file_path}")
            
            # Extract text from document
            document_text = extract_text_from_file(file_path)
            
            if not document_text or len(document_text.strip()) < 10:
                logger.warning(f"Insufficient text extracted from {file_path}")
                return ClassificationResult(
                    document_type=DocumentType.UNKNOWN,
                    confidence=0.0,
                    reasoning="Unable to extract sufficient text from document",
                    metadata={}
                )

            # Truncate text if too long (to avoid token limits)
            max_chars = 10000
            if len(document_text) > max_chars:
                document_text = document_text[:max_chars] + "\n... (truncated)"

            # Create the prompt
            messages = self.prompt_template.format_messages(
                filename=file_path.split("/")[-1],
                document_text=document_text
            )

            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse response
            result = self._parse_classification_response(response.content)
            
            logger.info(
                f"Classification complete: {result.document_type} "
                f"(confidence: {result.confidence:.2f})"
            )
            
            return result

        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                reasoning=f"Error during classification: {str(e)}",
                metadata={}
            )

    def _parse_classification_response(self, response_text: str) -> ClassificationResult:
        """
        Parse LLM response into ClassificationResult.

        Args:
            response_text: Raw LLM response text

        Returns:
            ClassificationResult object
        """
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Map document_type string to enum
            doc_type_str = data.get("document_type", "unknown").lower()
            if doc_type_str == "invoice":
                doc_type = DocumentType.INVOICE
            elif doc_type_str == "non_invoice":
                doc_type = DocumentType.NON_INVOICE
            else:
                doc_type = DocumentType.UNKNOWN
            
            return ClassificationResult(
                document_type=doc_type,
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", ""),
                metadata=data.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Fallback: try to determine from text content
            response_lower = response_text.lower()
            if "invoice" in response_lower and "not" not in response_lower[:100]:
                return ClassificationResult(
                    document_type=DocumentType.INVOICE,
                    confidence=0.5,
                    reasoning="Detected 'invoice' in response text (parsing failed)",
                    metadata={}
                )
            else:
                return ClassificationResult(
                    document_type=DocumentType.NON_INVOICE,
                    confidence=0.5,
                    reasoning="Could not parse structured response",
                    metadata={}
                )
