import boto3
from xilos.xget.contract import DataFetcher

from xilos.settings import logger


class AWSFetcher(DataFetcher):
    """Fetcher for AWS S3."""

    def __init__(self, region_name: str | None = None):
        self.s3 = boto3.client("s3", region_name=region_name)

    def fetch(self, source: str, **kwargs) -> bytes:
        """
        Fetch from S3.
        
        Args:
            source (str): s3://bucket/key format.
        """
        if source.startswith("s3://"):
            source = source[5:]

        bucket_name, key = source.split("/", 1)

        logger.debug(f"Downloading key {key} from bucket {bucket_name}")
        obj = self.s3.get_object(Bucket=bucket_name, Key=key)
        return obj["Body"].read()

    def fetch_to_file(self, source: str, destination_path: str, **kwargs) -> None:
        if source.startswith("s3://"):
            source = source[5:]
        bucket_name, key = source.split("/", 1)

        logger.info(f"Downloading {source} to {destination_path}")
        self.s3.download_file(bucket_name, key, destination_path)


class DynamoDBFetcher(DataFetcher):
    """Fetcher for AWS DynamoDB."""

    def __init__(self, region_name: str | None = None):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)

    def fetch(self, source: str, **kwargs) -> list[dict]:
        """
        Fetch items from DynamoDB table.
        
        Args:
            source (str): Table name.
            **kwargs: Arguments to pass to table.scan() (e.g., FilterExpression).
        
        Returns:
            list[dict]: List of items.
        """
        table = self.dynamodb.Table(source)
        logger.debug(f"Scanning DynamoDB table {source}")

        response = table.scan(**kwargs)
        data = response.get('Items', [])

        # Handle pagination if LastEvaluatedKey is present
        while 'LastEvaluatedKey' in response:
            logger.debug("Scanning next page...")
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'], **kwargs)
            data.extend(response.get('Items', []))

        return data
