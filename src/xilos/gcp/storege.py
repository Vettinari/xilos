from typing import Any
from google.cloud import storage
from google.cloud import bigquery
import pandas as pd
from xilos.xstore.contract import DataSaver
from xilos.settings import logger


class GCSSaver(DataSaver):
    """Saver for Google Cloud Storage."""

    def __init__(self, project_id: str | None = None):
        self.client = storage.Client(project=project_id)

    def save(self, data: Any, destination: str, **kwargs) -> None:
        """
        Upload data to GCS.

        Args:
            data (Any): Bytes or string.
            destination (str): URI (gs://bucket/blob) or path.
        """
        if destination.startswith("gs://"):
            destination = destination[5:]

        bucket_name, blob_name = destination.split("/", 1)

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        logger.debug(f"Uploading to blob {blob_name} in bucket {bucket_name}")

        if isinstance(data, str):
            blob.upload_from_string(data)
        elif isinstance(data, bytes):
            blob.upload_from_string(data)
        else:
            # Try converting to string
            blob.upload_from_string(str(data))

    def save_from_file(self, file_path: str, destination: str, **kwargs) -> None:
        if destination.startswith("gs://"):
            destination = destination[5:]
        bucket_name, blob_name = destination.split("/", 1)

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        logger.info(f"Uploading file {file_path} to {destination}")
        blob.upload_from_filename(file_path)


class BigQuerySaver(DataSaver):
    """Saver for Google BigQuery."""

    def __init__(self, project_id: str | None = None):
        self.client = bigquery.Client(project=project_id)

    def save(self, data: pd.DataFrame, destination: str, **kwargs) -> None:
        """
        Upload dataframe to BigQuery table.

        Args:
            data (pd.DataFrame): Data to upload.
            destination (str): Table ID (project.dataset.table).
        """
        logger.debug(f"Uploading DataFrame to BQ table {destination}")

        job_config = bigquery.LoadJobConfig(
            # Default to append, user can override via kwargs if needed in more complex impl
            write_disposition="WRITE_APPEND"
        )

        job = self.client.load_table_from_dataframe(
            data, destination, job_config=job_config
        )
        job.result()  # Wait for the job to complete.
        logger.info(f"Uploaded {len(data)} rows to {destination}.")

    def save_from_file(self, file_path: str, destination: str, **kwargs) -> None:
        """
        Upload CSV/Parquet file to BigQuery.
        """
        logger.info(f"Uploading file {file_path} to BQ table {destination}")

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV if file_path.endswith(".csv") else bigquery.SourceFormat.PARQUET,
            write_disposition="WRITE_APPEND",
            autodetect=True
        )

        with open(file_path, "rb") as source_file:
            job = self.client.load_table_from_file(source_file, destination, job_config=job_config)

        job.result()
        logger.info(f"Uploaded file to {destination}.")
