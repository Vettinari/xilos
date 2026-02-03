import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings

# Calculate project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_TYPES = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Parse xilos.toml if exists
CONFIG_PATH = PROJECT_ROOT / "xilos.toml"
PROJECT_CONFIG = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "rb") as f:
        PROJECT_CONFIG = tomllib.load(f)


class XProjectSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # General
    app_name: str = Field(default=PROJECT_CONFIG.get("project", {}).get("name", "XilosApp"))
    log_level: LOG_TYPES = Field(default="INFO", description="Logging level")

    # Cloud Config (defaults from xilos.toml or env)
    cloud_provider: str = Field(
        default=PROJECT_CONFIG.get("cloud", {}).get("provider", "local"),
        description="Cloud Provider",
    )

    cloud_storage: str = Field(
        default=PROJECT_CONFIG.get("cloud", {}).get("source", "local"),
        description="Storage Service",
    )

    # Observability
    log_destination: str = Field(
        default="xilos-logs", description="Destination for request logs (bucket/table/container)"
    )

    class Config:
        env_file = ".env"


core_settings = XProjectSettings()

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    level=core_settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
