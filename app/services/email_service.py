"""Email service for interacting with Microsoft Graph API."""

import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from msal import ConfidentialClientApplication
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

from app.config import get_settings
from app.models import EmailMessage, Attachment
from app.utils.logger import get_logger
from app.utils.security import sanitize_filename

logger = get_logger()


class EmailService:
    """Service for managing Outlook emails via Microsoft Graph API."""

    def __init__(self):
        """Initialize email service with Microsoft Graph credentials."""
        self.settings = get_settings()
        self.credential = ClientSecretCredential(
            tenant_id=self.settings.azure_tenant_id,
            client_id=self.settings.azure_client_id,
            client_secret=self.settings.azure_client_secret,
        )
        self.client = GraphServiceClient(credentials=self.credential)

    async def get_recent_emails(
        self, max_count: int = 10, unread_only: bool = True
    ) -> List[EmailMessage]:
        """
        Fetch recent emails from Outlook.

        Args:
            max_count: Maximum number of emails to retrieve
            unread_only: If True, only fetch unread emails

        Returns:
            List of EmailMessage objects
        """
        try:
            logger.info(f"Fetching up to {max_count} emails (unread_only={unread_only})")
            
            # Build query parameters
            query_params = {
                "$top": max_count,
                "$orderby": "receivedDateTime DESC",
            }
            
            if unread_only:
                query_params["$filter"] = "isRead eq false"

            # Get messages from the user's mailbox
            messages = await self.client.users.by_user_id(
                self.settings.user_email
            ).messages.get(query_parameters=query_params)

            email_messages = []
            
            if messages and messages.value:
                for msg in messages.value:
                    # Parse attachments
                    attachments = []
                    if msg.has_attachments:
                        # Get attachments for this message
                        msg_attachments = await self.client.users.by_user_id(
                            self.settings.user_email
                        ).messages.by_message_id(msg.id).attachments.get()
                        
                        if msg_attachments and msg_attachments.value:
                            for att in msg_attachments.value:
                                attachments.append(
                                    Attachment(
                                        name=att.name,
                                        size=att.size or 0,
                                        content_type=att.content_type or "application/octet-stream",
                                        attachment_id=att.id,
                                    )
                                )

                    email_message = EmailMessage(
                        id=msg.id,
                        subject=msg.subject or "",
                        sender=msg.from_.email_address.address if msg.from_ and msg.from_.email_address else "",
                        received_at=msg.received_date_time,
                        has_attachments=msg.has_attachments or False,
                        attachments=attachments,
                    )
                    email_messages.append(email_message)

            logger.info(f"Retrieved {len(email_messages)} emails")
            return email_messages

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    async def download_attachment(
        self, email_id: str, attachment_id: str, save_path: Path
    ) -> str:
        """
        Download an email attachment.

        Args:
            email_id: Email message ID
            attachment_id: Attachment ID
            save_path: Path where to save the attachment

        Returns:
            Full path to the saved file
        """
        try:
            logger.info(f"Downloading attachment {attachment_id} from email {email_id}")
            
            # Sanitize the filename to prevent path traversal
            safe_filename = sanitize_filename(save_path.name)
            safe_save_path = save_path.parent / safe_filename
            
            # Get the attachment
            attachment = await self.client.users.by_user_id(
                self.settings.user_email
            ).messages.by_message_id(email_id).attachments.by_attachment_id(
                attachment_id
            ).get()

            # Ensure save directory exists
            safe_save_path.parent.mkdir(parents=True, exist_ok=True)

            # Save attachment content
            if hasattr(attachment, "content_bytes") and attachment.content_bytes:
                content = base64.b64decode(attachment.content_bytes)
                with open(safe_save_path, "wb") as f:
                    f.write(content)
                logger.info(f"Attachment saved to {safe_save_path}")
                return str(safe_save_path)
            else:
                raise ValueError("Attachment has no content")

        except Exception as e:
            logger.error(f"Error downloading attachment: {e}")
            raise

    async def mark_as_read(self, email_id: str) -> None:
        """
        Mark an email as read.

        Args:
            email_id: Email message ID
        """
        try:
            logger.info(f"Marking email {email_id} as read")
            
            # Update the message
            from msgraph.generated.models.message import Message
            message = Message()
            message.is_read = True
            
            await self.client.users.by_user_id(
                self.settings.user_email
            ).messages.by_message_id(email_id).patch(message)
            
            logger.info(f"Email {email_id} marked as read")

        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            raise
