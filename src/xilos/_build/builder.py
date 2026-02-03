from loguru import logger

from .. import xsettings
from .contracts import BuildContext, BuildStep


class ProjectBuilder:
    """Orchestrates the project build process using defined steps."""

    def __init__(self):
        self.settings = xsettings
        self.xilos_root = xsettings.XILOS_ROOT

        self.template_dir = self.xilos_root / "src" / "xilos" / "_template"
        self.target_dir = self.xilos_root / "composed" / self.settings.project.name

        self.steps: list[BuildStep] = []

    def register(self, step: BuildStep) -> "ProjectBuilder":
        """Add a step to the pipeline."""
        self.steps.append(step)
        return self

    def build(self) -> None:
        """Execute all registered steps."""
        context = BuildContext(
            settings=self.settings,
            xilos_root=self.xilos_root,
            template_dir=self.template_dir,
            target_dir=self.target_dir,
        )

        logger.info("Starting Build Process...")
        for step in self.steps:
            logger.info(f"Step: {step.name()}")
            try:
                step.execute(context)
            except Exception as e:
                logger.error(f"Build step '{step.name()}' failed: {e}")
                raise e

        logger.info("Build Process Completed Successfully.")
