"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4", description="OpenAI Model to use")

    # Microsoft Graph API Configuration
    azure_client_id: str = Field(..., description="Azure Client ID")
    azure_client_secret: str = Field(..., description="Azure Client Secret")
    azure_tenant_id: str = Field(..., description="Azure Tenant ID")
    user_email: str = Field(..., description="User's Outlook email address")

    # FastAPI Configuration
    api_host: str = Field(default="0.0.0.0", description="API Host")
    api_port: int = Field(default=8000, description="API Port")
    api_reload: bool = Field(default=False, description="API Auto-reload")

    # Storage Configuration
    storage_base_path: str = Field(default="./storage", description="Base storage path")
    invoices_folder: str = Field(default="invoices", description="Invoices folder name")
    others_folder: str = Field(default="others", description="Others folder name")
    temp_folder: str = Field(default="temp", description="Temp folder name")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/app.log", description="Log file path")

    # Email Monitoring
    email_check_interval: int = Field(default=300, description="Email check interval in seconds")
    max_emails_per_check: int = Field(default=10, description="Max emails to process per check")

    @property
    def invoices_path(self) -> Path:
        """Get full path to invoices folder."""
        return Path(self.storage_base_path) / self.invoices_folder

    @property
    def others_path(self) -> Path:
        """Get full path to others folder."""
        return Path(self.storage_base_path) / self.others_folder

    @property
    def temp_path(self) -> Path:
        """Get full path to temp folder."""
        return Path(self.storage_base_path) / self.temp_folder


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
