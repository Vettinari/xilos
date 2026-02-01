import abc
from typing import Optional, Union

import pandas as pd
import polars as pl
from loguru import logger

from . import settings


class DataStorage(abc.ABC):
    """Abstract base class for all data fetchers."""

    @abc.abstractmethod
    def fetch(self, source: str) -> pl.DataFrame:
        """Fetch data from the specified source."""

    @abc.abstractmethod
    def store(self, data: Optional[Union[pl.DataFrame, pd.DataFrame]], destination: str) -> None:
        """Save data to the destination."""

    def fetch_to_file(self, source: str, destination_path: str) -> None:
        logger.info(f"Fetching {source} to {destination_path}...")
        pl_data = self.fetch(source)
        pl_data.write_parquet(destination_path)
        logger.info("Fetch complete.")


def get_storage(provider: str | None = None, storage: str | None = None) -> DataStorage:
    """
    Factory to get the appropriate DataFetcher based on provider and storage.
    If provider/storage not provided, defaults to settings.
    """
    prov = provider or settings.cloud_provider
    stor = storage or settings.cloud_storage

    if prov == "aws":
        # Placeholder for AWS imports
        # from xilos.aws.storage import AWSFetcher, DynamoDBFetcher
        if stor == "s3":
            # return AWSFetcher()
            pass
        elif stor == "dynamodb":
            # return DynamoDBFetcher()
            pass
    elif prov == "gcp":
        from xilos.gcp.storage import GCSFetcher, BigQueryFetcher
        if stor == "gcs":
            return GCSFetcher()
        elif stor == "bigquery":
            return BigQueryFetcher()
    elif prov == "azure":
        # Placeholder for Azure imports
        # from xilos.azure.storage import AzureFetcher, CosmosDBFetcher
        if stor == "blob":
            # return AzureFetcher()
            pass
        elif stor == "cosmos":
            # return CosmosDBFetcher()
            pass

    raise ValueError(f"Unsupported provider/storage combination: {prov}/{stor} or local not implemented yet.")
