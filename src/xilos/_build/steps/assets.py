import shutil

from loguru import logger

from ..contracts import BuildContext, BuildStep


class BaseAssetsStep(BuildStep):
    def name(self) -> str:
        return "Asset Deployment (xroot)"

    def execute(self, context: BuildContext) -> None:
        logger.info("Deploying xroot files...")
        if not context.xroot_dir.exists():
            logger.warning(f"xroot directory not found at {context.xroot_dir}")
            return

        for item in context.xroot_dir.iterdir():
            if item.name in {"__init__.py", "__pycache__", "pyproject.toml", ".ruff_cache"}:
                # We skip pyproject.toml because we generate it
                continue

            destination = context.target_dir / item.name

            if item.is_file():
                shutil.copy2(item, destination)
                logger.debug(f"Copied {item.name} -> {destination}")
            elif item.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(
                    item, 
                    destination, 
                    ignore=shutil.ignore_patterns(".ruff_cache", "__pycache__")
                )
                logger.debug(f"Copied dir {item.name} -> {destination}")
