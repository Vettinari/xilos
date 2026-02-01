from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from loguru import logger
import sys
from pathlib import Path
from datetime import datetime
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Calculate project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

ENV_TYPES = Literal["dev", "stg", "prod"]
LOG_TYPES = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

DATA_DIR = PROJECT_ROOT / "data"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
MODEL_DIR = ARTIFACT_DIR / "models"
PROCESSOR_DIR = ARTIFACT_DIR / "processor"

DATA_DIR.mkdir(exist_ok=True)
ARTIFACT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
PROCESSOR_DIR.mkdir(exist_ok=True)

# Parse xilos.toml if exists
CONFIG_PATH = PROJECT_ROOT / "xilos.toml"
PROJECT_CONFIG = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "rb") as f:
        PROJECT_CONFIG = tomllib.load(f)

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # General
    app_name: str = "xilos"
    env: ENV_TYPES = Field(default="dev", description="Environment: dev, stg, prod")
    log_level: LOG_TYPES = Field(default="INFO", description="Logging level")
    
    # Training
    train_data_location: str = str(DATA_DIR / "train.csv")
    model_output_path: str = str(MODEL_DIR / f"model_{NOW}.pkl")
    processor_path: str = str(PROCESSOR_DIR / f"{NOW}_processor.json")
    random_seed: int = 42

    # Cloud Config (defaults from xilos.toml or env)
    cloud_provider: str = Field(default=PROJECT_CONFIG.get("cloud", {}).get("provider", "local"), description="Cloud Provider")
    cloud_storage: str = Field(default=PROJECT_CONFIG.get("cloud", {}).get("storage", "local"), description="Storage Service")
    
    # Observability
    log_destination: str = Field(default="xilos-logs", description="Destination for request logs (bucket/table/container)")

    class Config:
        env_file = ".env"

settings = Settings()

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)