from loguru import logger

from ..contracts import BuildContext, BuildStep


class StructureStep(BuildStep):
    def name(self) -> str:
        return "Structure Generation"

    def execute(self, context: BuildContext) -> None:
        logger.info(f"Generating project for {context.settings.project.name} at {context.target_dir}...")

        if not context.target_dir.exists():
            context.target_dir.mkdir(parents=True)
            logger.info(f"Created project directory: {context.target_dir}")
        else:
            logger.warning(
                f"Target directory {context.target_dir} already exists. Existing files may be overwritten."
            )

        # Create src/<package_name> structure
        pkg_dir = context.target_dir / "src" / context.package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created package directory: {pkg_dir}")
