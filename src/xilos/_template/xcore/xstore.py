import abc

import pandas as pd
import polars as pl
from loguru import logger

from ..config import DATA_DIR, NOW, ProjectConfig


class DataStorage(abc.ABC):
    """Abstract base class for all data fetchers."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def download_object(self, cloud_path: str, file_path: str) -> None:
        """Fetch an object from the specified path."""

    @abc.abstractmethod
    def store_object(self, file_path: str, cloud_path: str) -> None:
        """Save an object to the destination."""

    def download_dataframe(self, cloud_path: str, save_path: str | None = None) -> pl.DataFrame:
        logger.info(f"Fetching dataframe from {cloud_path}")
        try:
            temp_name = DATA_DIR / f"temp_{NOW}.parquet"
            self.download_object(
                cloud_path=cloud_path,
                file_path=save_path or DATA_DIR / temp_name,
            )
            df = pl.read_parquet(cloud_path)

            if save_path is None:
                import os

                os.remove(DATA_DIR / temp_name)

            return df

        except Exception as e:
            logger.error(f"S3 fetch failed: {e}")
            raise

    def store_dataframe(
        self,
        data: pl.DataFrame | pd.DataFrame | None,
        destination: str,
        cloud_path: str,
    ) -> None:
        """Save data to the destination."""
        logger.info(f"Storing dataframe to {destination}...")
        data.write_parquet(destination)
        self.store_object(file_path=destination, cloud_path=cloud_path)
        logger.info("Store complete.")

        if self.config.ENV != "dev":
            import os

            os.remove(destination)


class DataTable(abc.ABC):
    """Abstract base class for all data metrics loggers."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def query(self, source: str, query: str = None, store: bool = True) -> pl.DataFrame:
        """Fetch logged metrics from the specified source."""

    @abc.abstractmethod
    def append(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """Save data to the destination."""

    @abc.abstractmethod
    def create_table(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """Create a metrics table in the underlying store."""
