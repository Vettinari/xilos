from xilos._template.settings import ProjectConfig


class GCPConfig(ProjectConfig):
    REGION_NAME: str | None = None
    PROJECT_ID: str | None = None

    # Storage specific if needed
    GCP_BUCKET_NAME: str = "xilos-bucket"


gcp_config = GCPConfig()
