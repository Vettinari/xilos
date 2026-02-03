from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
import polars as pl
from azure.cosmos import CosmosClient
from azure.cosmos.aio import ContainerProxy, DatabaseProxy
from azure.storage.blob import BlobClient, BlobServiceClient
from loguru import logger

from ..xcore.xstore import DataStorage, DataTable
from .settings import AzureConfig


class AzureStorage(DataStorage):
    """Saver for Azure Blob Storage."""

    def __init__(self, config: AzureConfig) -> None:
        super().__init__(config)
        self._conn_str = config.AZURE_STORAGE_CONNECTION_STRING

    def download_object(self, cloud_path: str, file_path: str) -> None:
        """Download blob to local file."""
        with self.blob_client(self, cloud_path=cloud_path) as blob_client:
            logger.info(f"Downloading {cloud_path} to {file_path}")
            with open(file_path, "wb") as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())

    def store_object(self, file_path: str, cloud_path: str) -> None:
        """Upload local file to blob storage."""
        with self.blob_client(self, cloud_path=cloud_path) as blob_client:
            logger.info(f"Uploading {file_path} to {cloud_path}")
            with open(file_path, "rb") as f:
                blob_client.upload_blob(f, overwrite=True)

    @staticmethod
    def _parse_azure_path(path: str) -> tuple[str, str]:
        if path.startswith("abfs://"):
            path = path[7:]

        elif path.startswith("az://"):
            path = path[5:]

        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid Azure path: {path}")

        return parts[0], parts[1]

    @contextmanager
    def service_client(self) -> Generator[BlobServiceClient, Any, None]:
        """Get the underlying BlobServiceClient."""
        client = BlobServiceClient.from_connection_string(self._conn_str)

        try:
            yield client

        finally:
            client.close()
            del client

    @contextmanager
    def blob_client(self, cloud_path: str) -> Generator[BlobClient, Any, None]:
        container, blob = self._parse_azure_path(cloud_path)

        with self.service_client(self) as sclient:
            blob_client = sclient.get_blob_client(container=container, blob=blob)

            try:
                yield blob_client

            finally:
                blob_client.close()

            del blob_client


class CosmosStorage(DataTable):
    """Saver for Azure Cosmos DB (SQL/Core API)."""

    def __init__(self, config: AzureConfig) -> None:
        super().__init__(config)
        self._url = config.AZURE_COSMOS_URL
        self._key = config.AZURE_COSMOS_KEY

    def query(self, source: str, query: str = None, store: bool = True) -> pl.DataFrame:
        """
        Fetch items from Cosmos container.
        Args:
            source: database/container
            query: SQL query
            store: whether to store or not
        """
        with self.container_client(self, source) as cclient:
            sql = query if query else "SELECT * FROM c"

            # Simple query for all items
            items = list(cclient.query_items(query=sql, enable_cross_partition_query=True))
            return pl.DataFrame(items)

    def append(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """
        Save items to Cosmos DB container.
        Args:
            destination (str): database_name/container_name
        """
        if data is None:
            return

        database_name, container_name = destination.split("/", 1)
        with self.container_client(self, source=destination) as container_client:
            if isinstance(data, pl.DataFrame):
                records = data.to_dicts()
            else:
                records = data.to_dict(orient="records")

            logger.debug(f"Creating items in Cosmos DB container {container_name}")
            for item in records:
                container_client.create_item(body=item)

    def create_table(self, data: pl.DataFrame | pd.DataFrame | None, destination: str) -> None:
        """
        Create a Cosmos container.
        For exact parity, this should check if container exists or create it.
        Requires database name and container name.
        """
        with self.db_client(self, source=destination) as db_client:
            try:
                from azure.cosmos import PartitionKey

                _, container_name = self._source_to_db_and_container(source=destination)
                db_client.create_container(id=container_name, partition_key=PartitionKey(path="/id"))
                logger.info(f"Created container {container_name}")

            except Exception as e:
                logger.warning(f"Container creation failed (might exist): {e}")

    @contextmanager
    def container_client(self, source: str) -> Generator[ContainerProxy, Any, None]:
        _, container_name = self._source_to_db_and_container(source=source)

        with self.db_client(self, source=source) as db_client:
            container_client = db_client.get_container_client(container_name)

            try:
                yield container_client

            finally:
                del container_client, db_client

    @contextmanager
    def db_client(self, source: str) -> Generator[DatabaseProxy, Any, None]:
        db_name, _ = self._source_to_db_and_container(source=source)

        cosmos_client = CosmosClient(self._url, credential=self._key)
        db_client = cosmos_client.get_database_client(db_name)

        try:
            yield db_client

        finally:
            del cosmos_client, db_client

    @staticmethod
    def _source_to_db_and_container(source: str) -> tuple[str, str]:
        parts = source.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid Cosmos DB source format: {source}, must be database/container")

        return parts[0], parts[1]
