import asyncio
from minio import Minio
from minio.error import S3Error
from authorization_service.core.config import settings
import io

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created successfully.")
        except S3Error as err:
            print(f"Error checking/creating bucket: {err}")
            raise

    async def upload_file(self, object_name: str, file_data: bytes, content_type: str):
        data_stream = io.BytesIO(file_data)
        loop = asyncio.get_event_loop()

        def upload():
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                len(file_data),
                content_type=content_type
            )

        await loop.run_in_executor(None, upload)
        return {"message": f"File {object_name} uploaded successfully.", "object_name": object_name}

    async def download_file(self, object_name: str):
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as err:
            print(f"Error downloading file: {err}")
            raise
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

    async def delete_file(self, object_name: str):
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return {"message": f"File {object_name} deleted successfully."}
        except S3Error as err:
            print(f"Error deleting file: {err}")
            raise
