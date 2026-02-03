from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from .. import XilosSettings


@dataclass
class BuildContext:
    """Holds shared state and configuration for the build process."""

    settings: XilosSettings
    xilos_root: Path
    template_dir: Path
    target_dir: Path
    generated_files: list[Path] = field(default_factory=list)

    @property
    def xroot_dir(self) -> Path:
        return self.template_dir / "xroot"

    @property
    def xrepos_dir(self) -> Path:
        return self.template_dir / "xrepos"

    @property
    def package_name(self) -> str:
        return self.settings.project.package_name


@runtime_checkable
class BuildStep(Protocol):
    """Interface for a step in the project generation process."""

    def name(self) -> str:
        """Name of the step for logging."""

    def execute(self, context: BuildContext) -> None:
        """Execute the step logic."""
