import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import numpy as np
from loguru import logger
from pydantic_settings import BaseSettings

# Calculate project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

MODEL_DIR: Path = Path("./models")
DATA_DIR: Path = Path("./data")
ARTIFACTS_DIR: Path = Path("./artifacts")

for dir_path in [MODEL_DIR, DATA_DIR, ARTIFACTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

LOG_TYPES = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ProjectConfig(BaseSettings):
    """Application settings loaded from environment variables."""

    ENV: Literal["dev", "stg", "prod"] = "dev"
    LOG_LEVEL: LOG_TYPES = "INFO"

    MODEL_PATH: str = (MODEL_DIR / f"{NOW}_model").as_posix()
    PROCESSOR_PATH: str = (DATA_DIR / f"{NOW}_processor").as_posix()

    SERVE_HOST: str = ""
    SERVE_PORT: int = 8000

    RANDOM_SEED: int = 42

    class Config:
        env_file = ".env"


project_config = ProjectConfig()

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    level=project_config.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

np.random.seed(project_config.RANDOM_SEED)
random.seed(project_config.RANDOM_SEED)
