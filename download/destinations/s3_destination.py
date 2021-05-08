import os

import boto3

from download.destinations.basic_destination import BasicDestination


class S3Destination(BasicDestination):

    s3_client = None

    def __init__(self):
        self.s3_bucket = os.environ.get("S3_BUCKET")

        # Instantiate and S3 client
        self.s3_client = boto3.session.Session().client(
            service_name="s3",
            region_name=os.environ.get("S3_REGION"),
            use_ssl=True,
            endpoint_url=os.environ.get("S3_ENDPOINT"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

    def save(self, downloaded_binary, source, name, url, **kwargs):
        self.s3_client.put_object(
            Bucket=self.s3_bucket, Key=name, Body=downloaded_binary
        )
