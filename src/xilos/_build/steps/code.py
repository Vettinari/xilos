import shutil

from loguru import logger

from ..contracts import BuildContext, BuildStep


class CodeDeployStep(BuildStep):
    def name(self) -> str:
        return "Code Deployment"

    def execute(self, context: BuildContext) -> None:
        logger.info("Deploying code modules...")
        
        target_pkg_dir = context.target_dir / "src" / context.package_name

        # 1. Copy top-level files (__init__.py, settings.py)
        for filename in ["__init__.py", "settings.py"]:
            src = context.template_dir / filename
            if src.exists():
                shutil.copy2(src, target_pkg_dir / filename)
                logger.debug(f"Copied {filename}")

        # 2. Copy Standard Modules
        modules = ["xcore", "xtrain", "xserve", "xmonitor"]

        for mod in modules:
            src = context.template_dir / mod
            dest = target_pkg_dir / mod
            if src.exists():
                if dest.exists():
                    shutil.rmtree(dest)

                # Copy tree but ignore pyproject.toml and caches
                shutil.copytree(
                    src, 
                    dest, 
                    ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__", ".ruff_cache")
                )
                logger.info(f"Deployed module: {mod}")
            else:
                logger.warning(f"Module {mod} not found in template")

        # 3. Copy Provider Module
        provider_module = f"x{context.settings.cloud.provider}"
        src = context.template_dir / provider_module
        dest = target_pkg_dir / provider_module

        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(
                src, 
                dest, 
                ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__", ".ruff_cache")
            )
            logger.info(f"Deployed provider module: {provider_module}")
        else:
            logger.warning(f"Provider module {provider_module} not found in template")
