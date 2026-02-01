from xilos._template.settings import ProjectConfig


class AWSConfig(ProjectConfig):
    REGION_NAME: str | None = None

aws_config = AWSConfig()