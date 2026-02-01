import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings

import tomllib

# Calculate project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_TYPES = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class ProjectSettings(BaseSettings):
    """Application settings loaded from environment variables."""
    log_level: LOG_TYPES = Field(default="INFO", description="Logging level")

    # Observability
    log_destination: str = Field(
        default="xilos-logs", description="Destination for request logs (bucket/table/container)"
    )

    class Config:
        env_file = ".env"


project_settings = ProjectSettings()

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    level=project_settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
