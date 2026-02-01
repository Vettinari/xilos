import shutil

from loguru import logger

from ..xilos_settings import xsettings


class ProjectGenerator:
    def __init__(self):
        self.settings = xsettings
        self.xilos_root = xsettings.XILOS_ROOT

        # Define source directories - UPDATED to use _template
        self.template_dir = self.xilos_root / "src" / "xilos" / "_template"
        self.xroot_dir = self.template_dir / "xroot"
        self.xrepos_dir = self.template_dir / "xrepos"

        # Define target
        self.target_dir = self.xilos_root / 'composed' /self.settings.project.name

    def run(self):
        self.init_structure()
        self.deploy_xroot()
        self.deploy_pipelines()
        self.deploy_code()
        self.generate_pyproject()
        logger.info("Project generation complete.")

    def init_structure(self):
        logger.info(f"Generating project for {self.settings.project.name} at {self.target_dir}...")

        if not self.target_dir.exists():
            self.target_dir.mkdir(parents=True)
            logger.info(f"Created project directory: {self.target_dir}")
        else:
            logger.warning(f"Target directory {self.target_dir} already exists. Existing files may be overwritten.")

        # Create src/xilos structure
        (self.target_dir / "src" / "xilos").mkdir(parents=True, exist_ok=True)

    def deploy_code(self):
        """Copies code modules from _template to src/xilos."""
        logger.info("Deploying code modules...")

        target_pkg_dir = self.target_dir / "src" / "xilos"

        # 1. Copy top-level files (__init__.py, settings.py)
        for filename in ["__init__.py", "settings.py"]:
            src = self.template_dir / filename
            if src.exists():
                shutil.copy2(src, target_pkg_dir / filename)
                logger.debug(f"Copied {filename}")

        # 2. Copy Standard Modules
        modules = ["xcore", "xtrain", "xserve", "xmonitor"]

        for mod in modules:
            src = self.template_dir / mod
            dest = target_pkg_dir / mod
            if src.exists():
                if dest.exists():
                    shutil.rmtree(dest)

                # Copy tree but ignore pyproject.toml and __pycache__
                shutil.copytree(src, dest, ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__"))
                logger.info(f"Deployed module: {mod}")
            else:
                logger.warning(f"Module {mod} not found in template")

        # 3. Copy Provider Module
        provider_module = f"x{self.settings.cloud.provider}"
        src = self.template_dir / provider_module
        dest = target_pkg_dir / provider_module

        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__"))
            logger.info(f"Deployed provider module: {provider_module}")
        else:
            logger.warning(f"Provider module {provider_module} not found in template")

    def deploy_xroot(self):
        """Copies default image building and root files from xroot."""
        logger.info("Deploying xroot files...")
        if not self.xroot_dir.exists():
            logger.warning(f"xroot directory not found at {self.xroot_dir}")
            return

        for item in self.xroot_dir.iterdir():
            if item.name == "__init__.py" or item.name == "__pycache__" or item.name == "pyproject.toml":
                # We skip pyproject.toml because we generate it
                continue

            destination = self.target_dir / item.name

            if item.is_file():
                shutil.copy2(item, destination)
                logger.debug(f"Copied {item.name} -> {destination}")
            elif item.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(item, destination)
                logger.debug(f"Copied dir {item.name} -> {destination}")

    def deploy_pipelines(self):
        """Copies pipelines based on repository configuration."""
        repo_type = self.settings.repository.type
        logger.info(f"Deploying pipelines for repository type: {repo_type}")

        source_repo_dir = self.xrepos_dir / repo_type
        if not source_repo_dir.exists():
            logger.warning(f"Repository source not found for type {repo_type} at {source_repo_dir}")
            return

        # Simple recursive copy of everything in the repo dir to target dir
        shutil.copytree(
            source_repo_dir,
            self.target_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__init__.py", "__pycache__"),
        )
        logger.info(f"Copied pipeline files from {source_repo_dir}")

    def generate_pyproject(self):
        """Merges pyproject.toml files from base, provider, and modules."""
        logger.info("Generating pyproject.toml...")
        import tomllib
        from .._build.toml_merger import deep_merge, to_toml_string

        # 1. Base pyproject (src/xilos/pyproject.toml)
        base_pyproject_path = self.xilos_root / "src" / "xilos" / "_template" / "pyproject.toml"
        if not base_pyproject_path.exists():
            logger.error(f"Base pyproject.toml not found at {base_pyproject_path}")
            return

        with open(base_pyproject_path, "rb") as f:
            config = tomllib.load(f)

        # Update Project Meta from Settings
        if "tool" in config and "poetry" in config["tool"]:
            config["tool"]["poetry"]["name"] = self.settings.project.name
            config["tool"]["poetry"]["description"] = f"Values tailored for {self.settings.cloud.provider}"
            # Keep other defaults or update as needed

        # 2. Provider pyproject (src/xilos/_template/x{provider}/pyproject.toml)
        # Naming convention seems to be x{provider}, e.g., xgcp, xaws
        provider_module = f"x{self.settings.cloud.provider}"
        provider_pyproject_path = self.template_dir / provider_module / "pyproject.toml"

        if provider_pyproject_path.exists():
            logger.info(f"Merging provider config from {provider_module}")
            with open(provider_pyproject_path, "rb") as f:
                provider_config = tomllib.load(f)
            config = deep_merge(config, provider_config)
        else:
            logger.warning(f"No pyproject.toml found for provider module {provider_module}")

        # 3. Modules (xserve, etc.)
        # Hardcoded list of modules for now, or could be dynamic based on settings
        modules = ["xserve"]  # xmonitor, xtrain seem to not have their own yet or rely on base

        for mod in modules:
            mod_pyproject_path = self.template_dir / mod / "pyproject.toml"
            if mod_pyproject_path.exists():
                logger.info(f"Merging module config from {mod}")
                with open(mod_pyproject_path, "rb") as f:
                    mod_config = tomllib.load(f)
                config = deep_merge(config, mod_config)

        # Write final pyproject.toml
        target_path = self.target_dir / "pyproject.toml"
        with open(target_path, "w") as f:
            f.write(to_toml_string(config))
        logger.info(f"Written merged pyproject.toml to {target_path}")


if __name__ == "__main__":
    generator = ProjectGenerator()
    generator.run()
