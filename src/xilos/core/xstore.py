import abc
from typing import Optional

import pandas as pd
import polars as pl

from xilos.settings import logger
from xilos.settings import settings
from .aws import AWSFetcher, DynamoDBFetcher
from .azure import AzureFetcher, CosmosDBFetcher
from .gcp import GCSFetcher, BigQueryFetcher


class DataStorage(abc.ABC):
    """Abstract base class for all data fetchers."""

    @abc.abstractmethod
    def fetch(self, source: str) -> pl.DataFrame:
        """Fetch data from the specified source."""

    @abc.abstractmethod
    def store(self, data: Optional[pl.DataFrame, pd.Dataframe], destination: str) -> None:
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
        if stor == "s3":
            return AWSFetcher()
        elif stor == "dynamodb":
            return DynamoDBFetcher()
    elif prov == "gcp":
        if stor == "gcs":
            return GCSFetcher()
        elif stor == "bigquery":
            return BigQueryFetcher()
    elif prov == "azure":
        if stor == "blob":
            return AzureFetcher()
        elif stor == "cosmos":
            return CosmosDBFetcher()

    raise ValueError(f"Unsupported provider/storage combination: {prov}/{stor} or local not implemented yet.")


__all__ = [
    "DataStorage",
    "BigQueryFetcher",
    "AWSFetcher",
    "DynamoDBFetcher",
    "AzureFetcher",
    "CosmosDBFetcher",
    "get_storage",
]
