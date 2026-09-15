
import asyncio
import boto3
import structlog
from botocore.exceptions import ClientError
from backend.config import get_settings

logger = structlog.get_logger(__name__)

class S3Client:
    def __init__(self):
        self.settings = get_settings()
        # Initialize boto3 client synchronously
        if self.settings.AWS_ACCESS_KEY_ID and self.settings.AWS_SECRET_ACCESS_KEY:
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.settings.AWS_REGION
            )
        else:
            self.s3 = boto3.client("s3") # Uses default ~/.aws/credentials or IAM role
        self.bucket = self.settings.AWS_S3_BUCKET

    async def upload_file(self, file_content: bytes, s3_key: str) -> bool:
        """Upload a file to S3 securely."""
        def _upload():
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_content,
                ServerSideEncryption="AES256" # basic security
            )
        try:
            await asyncio.to_thread(_upload)
            return True
        except ClientError as e:
            logger.error("s3_upload_failed", error=str(e), s3_key=s3_key)
            return False

    async def download_file(self, s3_key: str) -> bytes:
        """Download a file from S3."""
        def _download():
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read()
        try:
            return await asyncio.to_thread(_download)
        except ClientError as e:
            logger.error("s3_download_failed", error=str(e), s3_key=s3_key)
            raise

    async def move_file(self, source_key: str, dest_key: str) -> bool:
        """Move a file from quarantine to processed."""
        def _move():
            copy_source = {"Bucket": self.bucket, "Key": source_key}
            self.s3.copy_object(CopySource=copy_source, Bucket=self.bucket, Key=dest_key)
            self.s3.delete_object(Bucket=self.bucket, Key=source_key)
        try:
            await asyncio.to_thread(_move)
            return True
        except ClientError as e:
            logger.error("s3_move_failed", error=str(e), source_key=source_key, dest_key=dest_key)
            return False

