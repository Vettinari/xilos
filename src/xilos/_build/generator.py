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
        self.target_dir = self.xilos_root / "composed" / self.settings.project.name

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

        # Create src/<package_name> structure
        pkg_name = self.settings.project.package_name
        (self.target_dir / "src" / pkg_name).mkdir(parents=True, exist_ok=True)

    def deploy_code(self):
        """Copies code modules from _template to src/<package_name>."""
        logger.info("Deploying code modules...")

        pkg_name = self.settings.project.package_name
        target_pkg_dir = self.target_dir / "src" / pkg_name

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

                # Copy tree but ignore pyproject.toml and caches
                shutil.copytree(
                    src, dest, ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__", ".ruff_cache")
                )
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
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns("pyproject.toml", "__pycache__", ".ruff_cache"))
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
            if item.name in {"__init__.py", "__pycache__", "pyproject.toml", ".ruff_cache"}:
                # We skip pyproject.toml because we generate it
                continue

            destination = self.target_dir / item.name

            if item.is_file():
                shutil.copy2(item, destination)
                logger.debug(f"Copied {item.name} -> {destination}")
            elif item.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(item, destination, ignore=shutil.ignore_patterns(".ruff_cache", "__pycache__"))
                logger.debug(f"Copied dir {item.name} -> {destination}")

    def deploy_pipelines(self):  # noqa: PLR0912
        """Copies pipelines based on repository configuration and merges with provider logic."""
        repo_type = self.settings.repository.type
        provider = self.settings.cloud.provider

        logger.info(f"Deploying pipelines for repo: {repo_type}, provider: {provider}")

        source_repo_dir = self.xrepos_dir / repo_type
        if not source_repo_dir.exists():
            logger.warning(f"Repository source not found for type {repo_type} at {source_repo_dir}")
            return

        # Determine config mapping
        # Tuple: (source_filename_in_repo_dir, target_relative_path)
        config_map = {
            "github": ("ci.yml", ".github/workflows/ci.yml"),
            "gitlab": (".gitlab-ci.yml", ".gitlab-ci.yml"),
            "bitbucket": ("bitbucket-pipelines.yml", "bitbucket-pipelines.yml"),
        }

        if repo_type not in config_map:
            logger.warning(f"Unknown repository type {repo_type}. Copying blindly.")
            shutil.copytree(
                source_repo_dir,
                self.target_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__init__.py", "__pycache__", "xproviders", ".ruff_cache"),
            )
            return

        base_filename, target_rel_path = config_map[repo_type]
        base_src_path = source_repo_dir / base_filename
        target_full_path = self.target_dir / target_rel_path

        # 1. Copy everything EXCEPT the base CI file and xproviders dir
        for item in source_repo_dir.iterdir():
            if item.name == "xproviders":
                continue
            if item.name == base_filename:
                continue

            dest = self.target_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(
                    item, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".ruff_cache", "__pycache__")
                )
            else:
                shutil.copy2(item, dest)

        # 2. Merge and Write CI File
        if not base_src_path.exists():
            logger.error(f"Base CI file {base_filename} not found in {source_repo_dir}")
            return

        with open(base_src_path) as f:
            base_content = f.read()

        # Find provider snippet
        providers_dir = source_repo_dir / "xproviders"
        snippet_content = ""

        # Try standard name first, then 'x' prefix
        # e.g. gcp.yaml or xgcp.yaml
        candidates = [f"{provider}.yaml", f"x{provider}.yaml"]
        found_snippet = False

        if providers_dir.exists():
            for cand in candidates:
                cand_path = providers_dir / cand
                if cand_path.exists():
                    logger.info(f"Found provider CI snippet: {cand}")
                    with open(cand_path) as f:
                        snippet_content = f.read()
                    found_snippet = True
                    break

            if not found_snippet:
                logger.warning(f"No CI snippet found for provider {provider} in {candidates}")

        # Merge
        full_content = base_content + "\n" + snippet_content

        # Ensure target dir exists
        target_full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_full_path, "w") as f:
            f.write(full_content)

        logger.info(f"Generated {target_rel_path} with {provider} configuration.")

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
            config["tool"]["poetry"]["version"] = self.settings.project.version
            config["tool"]["poetry"]["description"] = self.settings.project.description
            config["tool"]["poetry"]["authors"] = self.settings.project.authors
            config["tool"]["poetry"]["readme"] = self.settings.project.readme

            # Update source package
            config["tool"]["poetry"]["packages"] = [{"include": self.settings.project.package_name, "from": "src"}]

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
