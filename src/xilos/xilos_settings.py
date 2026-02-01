import tomllib  # type: ignore
from pathlib import Path

from pydantic import BaseModel


# Define the path to xilos.toml.
# Assuming it's in the project root, 3 levels up from this file (src/xilos/core/settings.py -> src/xilos -> src -> root)
# Adjust if necessary based on where the valid toml is located relative to the package.

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


class DescriptiveSettings(BaseModel):
    name: str


class XilosSettings(BaseModel):
    XILOS_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_PATH: Path = XILOS_ROOT / "xilos.toml"
    project: DescriptiveSettings
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


try:
    xsettings = XilosSettings.load()
except FileNotFoundError:
    raise FileNotFoundError(f"xilos.toml not found. Please ensure it exists in project root.")
