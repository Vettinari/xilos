from contextlib import contextmanager
from typing import Optional, Union, Generator

import boto3
import pandas as pd
import polars as pl
from loguru import logger

from .settings import AWSConfig
from ..xcore.xstore import DataStorage, DataTable


class S3Storage(DataStorage):
    """Fetcher for AWS S3."""

    def __init__(self, config: AWSConfig):
        super().__init__(config)
        self.config = config

    def download_object(self, cloud_path: str, file_path: str) -> None:
        """
        Download a file from S3.
        Args:
            cloud_path: s3://bucket/key
            file_path: Local path
        """
        bucket, key = self._parse_s3_path(cloud_path)
        logger.info(f"Downloading {cloud_path} to {file_path}")

        with self.get_client(self) as s3:
            s3.download_file(Bucket=bucket, Key=key, Filename=file_path)

    def store_object(self, file_path: str, cloud_path: str) -> None:
        """
        Upload a file to S3.
        Args:
            file_path: Local path
            cloud_path: s3://bucket/key
        """
        bucket, key = self._parse_s3_path(cloud_path)
        logger.info(f"Uploading {file_path} to {cloud_path}")

        with self.get_client(self) as s3:
            s3.upload_file(Filename=file_path, Bucket=bucket, Key=key)

    @staticmethod
    def _validate_s3_path(path: str) -> str:
        if not path.startswith("s3://"):
            raise ValueError(f"Invalid S3 path: {path}, must start with s3://")
        return path

    def _parse_s3_path(self, path: str) -> tuple[str, str]:
        path = self._validate_s3_path(path=path)
        path = path.replace("s3://", "")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 path format: {path}, must be s3://bucket/key")

        return parts[0], parts[1]

    @contextmanager
    def get_client(self) -> Generator[..., None, None]:
        s3 = boto3.client("s3", region_name=self.config.REGION_NAME)
        try:
            yield s3

        finally:
            del s3


class DynamoStorage(DataTable):
    """Fetcher for AWS DynamoDB."""

    def __init__(self, config: AWSConfig):
        super().__init__(config)
        self.config = config
        self.dynamodb = boto3.resource("dynamodb", region_name=config.REGION_NAME)

    def query(self, source: str, query: str = None, store: bool = True) -> pl.DataFrame:
        """
        Fetch items from DynamoDB table and return as DataFrame.
        Args:
            source (str): Table name.
            query (str): Optional KeyConditionExpression or filter (simplified for now).
        """
        table = self.dynamodb.Table(source)
        logger.debug(f"Scanning DynamoDB table {source}")

        # robust implementation would handle query vs scan based on input
        response = table.scan()
        data = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response.get('Items', []))

        return pl.DataFrame(data)

    def append(self, data: Optional[Union[pl.DataFrame, pd.DataFrame]], destination: str) -> None:
        """Store rows to DynamoDB table."""
        if data is None:
            return

        if isinstance(data, pl.DataFrame):
            records = data.to_dicts()
        else:
            records = data.to_dict(orient="records")

        table = self.dynamodb.Table(destination)

        with table.batch_writer() as batch:
            for item in records:
                batch.put_item(Item=item)

    def create_table(self, data: Optional[Union[pl.DataFrame, pd.DataFrame]], destination: str) -> None:
        """
        Create a DynamoDB table. 
        Note: This is complex in DynamoDB (need schema definition). 
        For now, this is a placeholder or minimal implementation.
        """
        logger.warning("create_table not fully implemented for DynamoDB (requires schema inference).")
        pass
