from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
import polars as pl
from google.cloud import bigquery, storage
from google.cloud.storage import Blob
from loguru import logger

from ..xcore.xstore import DataStorage, DataTable


class GCSStorage(DataStorage):
    """Fetcher for Google Cloud Storage."""

    def __init__(self, config: Any = None):
        super().__init__(config)

    def download_object(self, cloud_path: str, file_path: str) -> None:
        """Download file from GCS."""
        with self.get_blob(self, cloud_path) as blob:
            logger.info(f"Downloading {cloud_path} to {file_path}")
            blob.download_to_filename(file_path)

    def store_object(self, file_path: str, cloud_path: str) -> None:
        """Upload file to GCS."""
        with self.get_blob(self, cloud_path) as blob:
            logger.info(f"Uploading {file_path} to {cloud_path}")
            blob.upload_from_filename(file_path)

    @staticmethod
    def _parse_gcs_path(path: str) -> tuple[str, str]:
        if not path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {path}")
        path = path.replace("gs://", "")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GCS path format: {path}")
        return parts[0], parts[1]

    @contextmanager
    def get_blob(self, cloud_path: str) -> Generator[Blob, None, None]:
        """Get the underlying GCS client."""
        client = storage.Client()
        bucket_name, blob_name = self._parse_gcs_path(cloud_path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        try:
            yield blob

        finally:
            client.close()
            del client, bucket, blob


class BigQueryFetcher(DataTable):
    """Fetcher/Storer for BigQuery."""

    def __init__(self, config: Any = None):
        super().__init__(config)

    def query(self, source: str, query: str = None, store: bool = True) -> pl.DataFrame:
        """
        Fetch from BigQuery table.
        Args:
            source: Table ID (project.dataset.table) or if query is provided, this might be ignored or part of query context.
            query: SQL query string. If None, selects * from source.
        """
        sql = query
        if not sql:
            sql = f"SELECT * FROM `{source}`"

        logger.info(f"Querying BigQuery: {sql}")

        try:
            # Run query and download to Polars via Arrow (efficient)
            # Requires google-cloud-bigquery-storage and db-dtypes
            return pl.from_pandas(self.client.query(sql).to_dataframe())
        except Exception as e:
            logger.error(f"BigQuery query failed: {e}")
            raise

    def append(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """
        Store data to BigQuery table.
        Args:
            destination: Table ID (dataset.table).
        """
        logger.info(f"Storing to BigQuery: {destination}")
        if data is None:
            return

        if isinstance(data, pl.DataFrame):
            data = data.to_pandas()

        job_config = self.client.LoadJobConfig(write_disposition="WRITE_APPEND")

        try:
            job = self.client.load_table_from_dataframe(data, destination, job_config=job_config)
            job.result()  # Wait for completion
            logger.info(f"Loaded {len(data)} rows to {destination}")
        except Exception as e:
            logger.error(f"BigQuery store failed: {e}")
            raise

    def create_table(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """Create BigQuery table from dataframe schema."""
        logger.info(f"Creating BigQuery table: {destination}")
        if data is None:
            return

        if isinstance(data, pl.DataFrame):
            data = data.to_pandas()

        job_config = self.client.LoadJobConfig(write_disposition="WRITE_TRUNCATE")  # Create/Replace

        try:
            job = self.client.load_table_from_dataframe(data, destination, job_config=job_config)
            job.result()
            logger.info(f"Created table {destination}")
        except Exception as e:
            logger.error(f"BigQuery create table failed: {e}")
            raise

    @contextmanager
    def bigquery_client(self) -> Any:
        """Get the underlying GCS client."""
        client = bigquery.Client()

        try:
            yield client

        finally:
            client.close()
            del client
