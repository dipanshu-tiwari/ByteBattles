import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from fastapi import UploadFile

from config import S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_SIGNATURE_VERSION, TESTCASE_BUCKET, SUBMISSION_BUCKET

class StorageServiceTestcases:

    def __init__(self, bucket_name):

        self.bucket_name = bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
            config=Config(signature_version=S3_SIGNATURE_VERSION)
        )

    def _generate_object_key(self, problem_id: str, filename: str):
        unique_id = uuid.uuid4().hex
        return f"problems/{problem_id}/{unique_id}-{filename}"

    async def upload_file(self, problem_id: str, file: UploadFile):

        object_key = self._generate_object_key(problem_id, file.filename)
        contents = await file.read()

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=contents,
            ContentType=file.content_type
        )

        return object_key

    def upload_bytes(self, problem_id: str, filename: str, data: bytes):

        object_key = self._generate_object_key(problem_id, filename)

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=data
        )

        return object_key

    def get_file(self, object_key: str):

        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

        return response["Body"].read()

    def file_exists(self, object_key: str):
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False

    def delete_file(self, object_key: str):
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

    def delete_problem_folder(self, problem_id: str):

        prefix = f"problems/{problem_id}/"

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        contents = response.get("Contents", [])

        if not contents:
            return

        objects = [
            {"Key": obj["Key"]}
            for obj in contents
        ]

        self.client.delete_objects(
            Bucket=self.bucket_name,
            Delete={
                "Objects": objects
            }
        )

class StorageServiceSubmissionCode:

    def __init__(self, bucket_name):

        self.bucket_name = bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
            config=Config(signature_version=S3_SIGNATURE_VERSION)
        )

    def _generate_object_key(self, extension: str):
        unique_id = uuid.uuid4().hex
        return f"{unique_id}.{extension}"

    def upload_bytes(self, extension: str, data: bytes):

        object_key = self._generate_object_key(extension)

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=data
        )

        return object_key

    def get_file(self, object_key: str):

        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

        return response["Body"].read()

    def file_exists(self, object_key: str):
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False
    
    def delete_file(self, object_key: str):
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

storage_testcases = StorageServiceTestcases(TESTCASE_BUCKET)
storage_submission_code = StorageServiceSubmissionCode(SUBMISSION_BUCKET)