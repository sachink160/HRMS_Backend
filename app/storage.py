"""
Storage service abstraction layer for handling file uploads.
Supports both local storage (development) and S3 (production).
"""
import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod
from fastapi import UploadFile, HTTPException, status
import boto3
from botocore.exceptions import ClientError
from app.logger import log_info, log_error

# Storage configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local").lower()  # 'local' or 's3'
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", None)  # For S3-compatible services like MinIO
S3_CDN_URL = os.getenv("S3_CDN_URL", None)  # Optional CDN URL for serving files

# Local storage configuration
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:8000")  # Base URL for local file serving

# File validation
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class StorageInterface(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        document_type: str
    ) -> str:
        """Upload a file and return the file path/URL."""
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Get the public URL for a file."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        pass
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file type and size."""
        if not file.filename:
            return False
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False
        
        return True


class LocalStorage(StorageInterface):
    """Local file system storage implementation."""
    
    def __init__(self, upload_dir: Path = UPLOAD_DIR, base_url: str = LOCAL_BASE_URL):
        self.upload_dir = upload_dir
        self.base_url = base_url
        self.upload_dir.mkdir(exist_ok=True)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        document_type: str
    ) -> str:
        """Save uploaded file locally and return the relative file path."""
        if not self.validate_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPG, PNG, and PDF files are allowed."
            )
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{user_id}_{document_type}_{uuid.uuid4()}{file_ext}"
        file_path = self.upload_dir / unique_filename
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 10MB."
            )
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        log_info(f"File saved locally: {file_path}")
        # Return relative path for database storage
        return f"uploads/{unique_filename}"
    
    def get_file_url(self, file_path: str) -> str:
        """Get the public URL for a locally stored file."""
        if not file_path:
            return ""
        
        # If it's already a full URL, return as is
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        
        # Remove 'uploads/' prefix if present
        relative_path = file_path.replace("uploads/", "").replace("uploads\\", "")
        
        # Return URL for local file serving
        return f"{self.base_url}/uploads/{relative_path}"
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from local storage."""
        try:
            # Handle both relative and absolute paths
            if file_path.startswith("uploads/"):
                full_path = Path(file_path)
            else:
                full_path = self.upload_dir / file_path.replace("uploads/", "").replace("uploads\\", "")
            
            if full_path.exists():
                full_path.unlink()
                log_info(f"File deleted locally: {full_path}")
                return True
            return False
        except Exception as e:
            log_error(f"Error deleting local file {file_path}: {str(e)}")
            return False


class S3Storage(StorageInterface):
    """AWS S3 storage implementation."""
    
    def __init__(
        self,
        bucket_name: str = S3_BUCKET_NAME,
        region: str = S3_REGION,
        access_key_id: str = S3_ACCESS_KEY_ID,
        secret_access_key: str = S3_SECRET_ACCESS_KEY,
        endpoint_url: Optional[str] = S3_ENDPOINT_URL,
        cdn_url: Optional[str] = S3_CDN_URL
    ):
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is required for S3 storage")
        
        self.bucket_name = bucket_name
        self.region = region
        self.cdn_url = cdn_url
        self.endpoint_url = endpoint_url
        
        # Initialize S3 client
        s3_config = {
            'region_name': region
        }
        
        if access_key_id and secret_access_key:
            s3_config['aws_access_key_id'] = access_key_id
            s3_config['aws_secret_access_key'] = secret_access_key
        
        if endpoint_url:
            s3_config['endpoint_url'] = endpoint_url
        
        self.s3_client = boto3.client('s3', **s3_config)
        
        # Verify bucket exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            log_info(f"S3 storage initialized for bucket: {bucket_name}")
        except ClientError as e:
            log_error(f"Error accessing S3 bucket {bucket_name}: {str(e)}")
            raise
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        document_type: str
    ) -> str:
        """Upload file to S3 and return the S3 key."""
        if not self.validate_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPG, PNG, and PDF files are allowed."
            )
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{user_id}_{document_type}_{uuid.uuid4()}{file_ext}"
        s3_key = f"documents/{user_id}/{unique_filename}"
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 10MB."
            )
        
        # Determine content type
        content_type = file.content_type or "application/octet-stream"
        if file_ext in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif file_ext == ".png":
            content_type = "image/png"
        elif file_ext == ".pdf":
            content_type = "application/pdf"
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                ACL='public-read'  # Make files publicly accessible
            )
            log_info(f"File uploaded to S3: {s3_key}")
            return s3_key
        except ClientError as e:
            log_error(f"Error uploading to S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            )
    
    def get_file_url(self, file_path: str) -> str:
        """Get the public URL for an S3 file."""
        if not file_path:
            return ""
        
        # If it's already a full URL, return as is
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        
        # If CDN URL is configured, use it
        if self.cdn_url:
            return f"{self.cdn_url}/{file_path}"
        
        # Generate S3 public URL
        if self.endpoint_url:
            # For S3-compatible services (MinIO, etc.)
            return f"{self.endpoint_url}/{self.bucket_name}/{file_path}"
        else:
            # Standard AWS S3 URL
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_path}"
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            log_info(f"File deleted from S3: {file_path}")
            return True
        except ClientError as e:
            log_error(f"Error deleting S3 file {file_path}: {str(e)}")
            return False


def get_storage() -> StorageInterface:
    """Factory function to get the appropriate storage implementation."""
    if STORAGE_TYPE == "s3":
        try:
            return S3Storage()
        except Exception as e:
            log_error(f"Failed to initialize S3 storage: {str(e)}")
            log_info("Falling back to local storage")
            return LocalStorage()
    else:
        return LocalStorage()


# Global storage instance
storage = get_storage()

