import boto3
from django.conf import settings

class S3Client:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the S3 client."""
        if cls._instance is None:
            cls._instance = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
        return cls._instance
