from contextlib import contextmanager
from typing import Generator

from fastapi import Request
from loguru import logger
from pydantic import BaseModel
from sklearn.base import ClassifierMixin

from .settings import project_config
from .xcore.xstore import DataStorage, DataTable
from .xtrain.model import MLModel
from .xtrain.processor import DataProcessor
from .xtrain.processor.example import ExampleProcessor


def _parse_project_providers() -> tuple[DataStorage, DataTable]:
    try:
        from .xaws.settings import aws_config
        from .xaws.storage import S3Storage, DynamoStorage
        return S3Storage(aws_config), DynamoStorage(aws_config)

    except ImportError:
        pass

    try:
        from .xgcp.settings import gcp_config
        from .xgcp.storage import GCSStorage, BigQueryFetcher
        return GCSStorage(gcp_config), BigQueryFetcher(gcp_config)
    except ImportError:
        pass

    try:
        from .xazure.settings import azure_config
        from .xazure.storage import AzureStorage, CosmosStorage
        return AzureStorage(azure_config), CosmosStorage(azure_config)
    except ImportError:
        pass

    raise ImportError("No cloud provider configuration found.")


class ProviderRegistry(BaseModel):
    model: type[ClassifierMixin,]
    processor: type[DataProcessor]
    storage_provider: DataStorage
    table_provider: DataTable

    @contextmanager
    def get_model(self, request: Request) -> Generator[MLModel, None, None]:
        import os
        mp = project_config.MODEL_PATH
        if os.path.exists(mp):
            model = self.model.load(mp)
            logger.info(f"Model loaded from {mp}")
            yield model
            del model

        else:
            logger.warning(
                f"Model file not found at {mp}. Predictions will fail.",
            )

    @contextmanager
    def get_processor(self, request: Request) -> Generator[DataProcessor, None, None]:
        try:
            import os
            pp = project_config.PROCESSOR_PATH
            if os.path.exists(pp):
                processor = self.processor.load(pp)
                logger.info(f"Processor loaded from {pp}")
                yield processor
                del processor

            else:
                logger.warning(
                    f"Processor file not found at {pp}. Predictions will fail.",
                )

        except Exception as e:
            logger.error(f"Failed to initialize processor: {e}")


storage_provider, table_provider = _parse_project_providers()

registry = ProviderRegistry(
    model=MLModel,
    processor=ExampleProcessor,
    storage_provider=storage_provider,
    table_provider=table_provider,
)
