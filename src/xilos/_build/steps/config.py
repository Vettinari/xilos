import tomllib

from loguru import logger

from ..contracts import BuildContext, BuildStep
from ..toml_merger import deep_merge, to_toml_string


class ConfigStep(BuildStep):
    def name(self) -> str:
        return "Configuration Generation (pyproject.toml)"

    def execute(self, context: BuildContext) -> None:
        logger.debug("Generating pyproject.toml...")

        # 1. Base pyproject (src/xilos/pyproject.toml)
        # Note: This path logic mirrors generator.py's
        # xilos_root -> src/xilos/_template/pyproject.toml
        base_pyproject_path = context.xilos_root / "src" / "xilos" / "_template" / "pyproject.toml"
        if not base_pyproject_path.exists():
            logger.error(f"Base pyproject.toml not found at {base_pyproject_path}")
            return

        with open(base_pyproject_path, "rb") as f:
            config = tomllib.load(f)

        # Update Project Meta from Settings
        if "tool" not in config:
            config["tool"] = {}
        if "poetry" not in config["tool"]:
            config["tool"]["poetry"] = {}

        config["tool"]["poetry"]["name"] = context.settings.project.name
        config["tool"]["poetry"]["version"] = context.settings.project.version
        config["tool"]["poetry"]["description"] = context.settings.project.description
        config["tool"]["poetry"]["authors"] = context.settings.project.authors
        config["tool"]["poetry"]["readme"] = context.settings.project.readme

        # Update source package
        config["tool"]["poetry"]["packages"] = [{"include": context.settings.project.package_name, "from": "src"}]

        # 2. Provider pyproject
        provider_module = f"x{context.settings.cloud.provider}"
        provider_pyproject_path = context.template_dir / provider_module / "pyproject.toml"

        if provider_pyproject_path.exists():
            logger.debug(f"Merging provider config from {provider_module}")
            with open(provider_pyproject_path, "rb") as f:
                provider_config = tomllib.load(f)
            config = deep_merge(config, provider_config)
        else:
            logger.warning(f"No pyproject.toml found for provider module {provider_module}")

        # 3. Modules (xserve, etc.)
        modules = ["xserve"]

        for mod in modules:
            mod_pyproject_path = context.template_dir / mod / "pyproject.toml"
            if mod_pyproject_path.exists():
                logger.debug(f"Merging module config from {mod}")
                with open(mod_pyproject_path, "rb") as f:
                    mod_config = tomllib.load(f)
                config = deep_merge(config, mod_config)

        # Write final pyproject.toml
        target_path = context.target_dir / "pyproject.toml"
        with open(target_path, "w") as f:
            f.write(to_toml_string(config))

        logger.info(f"Generated merged pyproject.toml to {target_path}")
