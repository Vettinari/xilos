import shutil

from loguru import logger

from ..contracts import BuildContext, BuildStep


class PipelineStep(BuildStep):
    def name(self) -> str:
        return "CI/CD Pipeline Configuration"

    def execute(self, context: BuildContext) -> None:
        """Copies pipelines based on repository configuration and merges with provider logic."""
        repo_type = context.settings.repository.type
        provider = context.settings.cloud.provider

        logger.debug(f"Deploying pipelines for repo: {repo_type}, provider: {provider}")

        source_repo_dir = context.xrepos_dir / repo_type
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
                context.target_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__init__.py", "__pycache__", "xproviders", ".ruff_cache"),
            )
            return

        base_filename, target_rel_path = config_map[repo_type]
        base_src_path = source_repo_dir / base_filename
        target_full_path = context.target_dir / target_rel_path

        # 1. Copy everything EXCEPT the base CI file and xproviders dir
        for item in source_repo_dir.iterdir():
            if item.name == "xproviders":
                continue
            if item.name == base_filename:
                continue

            dest = context.target_dir / item.name
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
                    logger.debug(f"Found provider CI snippet: {cand}")
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

        logger.info(f"Generated {target_rel_path} with {provider} configuration and repo: {repo_type}")
