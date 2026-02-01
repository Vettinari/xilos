import os
from typing import Any

from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from loguru import logger

from ..xcore.xstore import DataStorage


class AzureStorage(DataStorage):
    """Saver for Azure Blob Storage."""

    def __init__(self, connection_string: str | None = None):
        conn_str = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            raise ValueError("Azure connection string required.")
        self.service_client = BlobServiceClient.from_connection_string(conn_str)

    def save(self, data: Any, destination: str, **kwargs) -> None:
        """
        Upload blob.

        Args:
            destination (str): container/blob format.
        """
        container_name, blob_name = destination.split("/", 1)

        blob_client = self.service_client.get_blob_client(container=container_name, blob=blob_name)
        logger.debug(f"Uploading to blob {blob_name} in container {container_name}")

        blob_client.upload_blob(data, overwrite=True)

    def save_from_file(self, file_path: str, destination: str, **kwargs) -> None:
        container_name, blob_name = destination.split("/", 1)
        blob_client = self.service_client.get_blob_client(container=container_name, blob=blob_name)

        logger.info(f"Uploading file {file_path} to {destination}")
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)


class CosmosStorage(DataStorage):
    """Saver for Azure Cosmos DB (SQL/Core API)."""

    def __init__(self, url: str | None = None, key: str | None = None):
        url = url or os.getenv("AZURE_COSMOS_URL")
        key = key or os.getenv("AZURE_COSMOS_KEY")
        if not url or not key:
            raise ValueError("Azure Cosmos URL and Key required.")

        self.client = CosmosClient(url, credential=key)

    def save(self, data: dict, destination: str, **kwargs) -> None:
        """
        Save item to Cosmos DB container.

        Args:
            data (dict): The item to create (must contain 'id').
            destination (str): database_name/container_name
        """
        database_name, container_name = destination.split("/", 1)
        database = self.client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        logger.debug(f"Creating item in Cosmos DB container {container_name}")
        container.create_item(body=data)
