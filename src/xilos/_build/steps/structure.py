import shutil

from loguru import logger

from ..contracts import BuildContext, BuildStep


class StructureStep(BuildStep):
    def name(self) -> str:
        return "Structure Generation"

    def execute(self, context: BuildContext) -> None:
        logger.debug(f"Generating project structure for {context.settings.project.name} at {context.target_dir}...")

        if context.target_dir.exists():
            logger.warning(
                f"Target directory {context.target_dir} already exists. Would you like to overwrite it? (y/n)",
            )
            choice = input("> ")
            if choice.lower() == "y":
                shutil.rmtree(context.target_dir)

        # Create src/<package_name> structure
        pkg_dir = context.target_dir / "src" / context.package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created package directory: {pkg_dir}")
