import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloudSettings:
    provider: str


@dataclass
class RepositorySettings:
    type: str


@dataclass
class MonitorSettings:
    # Optional fields or with defaults if TOML might miss them
    numeric_threshold: float
    numerical: str
    categorical: str


@dataclass
class DescriptiveSettings:
    name: str
    package_name: str
    version: str
    description: str
    authors: list[str]
    readme: str


@dataclass
class XilosSettings:
    project: DescriptiveSettings
    cloud: CloudSettings
    repository: RepositorySettings
    monitor: MonitorSettings

    # Class-level constants
    XILOS_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_PATH: Path = XILOS_ROOT / "xilos.toml"

    @classmethod
    def load(cls) -> "XilosSettings":
        if not cls.CONFIG_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found at {cls.CONFIG_PATH}")

        with open(cls.CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)

        # Manually parse nested dicts into dataclasses
        try:
            return cls(
                project=DescriptiveSettings(**data.get("project", {})),
                cloud=CloudSettings(**data.get("cloud", {})),
                repository=RepositorySettings(**data.get("repository", {})),
                monitor=MonitorSettings(**data.get("monitor", {})),
            )
        except TypeError as e:
            # Handle missing keys or type mismatch gracefully-ish
            raise ValueError(f"Error loading configuration: {e}") from e


try:
    xsettings = XilosSettings.load()
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"xilos.toml not found at {XilosSettings.CONFIG_PATH}. Please ensure it exists in project root."
    ) from e
