import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "xilos.toml"

class CloudSettings(BaseModel):
    provider: str
    source: str
    metrics: str

class RepositorySettings(BaseModel):
    type: str

class MonitorSettings(BaseModel):
    numeric_threshold: float
    numerical: str
    categorical: str
    source: str
    metrics: str

class ProjectSettings(BaseModel):
    name: str

class Settings(BaseModel):
    project: ProjectSettings
    cloud: CloudSettings
    repository: RepositorySettings
    monitor: MonitorSettings

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Settings":
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found at {path}")
        
        with open(path, "rb") as f:
            data = tomllib.load(f)
        
        return cls(**data)

# Singleton instance
try:
    settings = Settings.load()
except FileNotFoundError:
    # Fallback or allow lazy loading if running in an environment without the file immediately
    # For now, we print a warning or handle it gracefully. 
    # But since this is a generator required file, strictly speaking we might want to fail.
    # We will instantiate a dummy or raise error when accessed if truly needed.
    settings = None # type: ignore

# Expose individual settings for easier import if needed, but 'settings' object is preferred
if settings:
    cloud_provider = settings.cloud.provider
    cloud_storage = settings.cloud.source
else:
    cloud_provider = None
    cloud_storage = None
