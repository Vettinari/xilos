from xilos._template.settings import ProjectConfig


class AzureConfig(ProjectConfig):
    REGION_NAME: str
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_COSMOS_URL: str
    AZURE_COSMOS_KEY: str


azure_config = AzureConfig()
