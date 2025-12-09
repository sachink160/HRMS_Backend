# Storage Setup Guide

This HRMS application supports two storage backends for document uploads:

1. **Local Storage** (Development) - Files stored in `uploads/` directory
2. **S3 Storage** (Production) - Files stored in AWS S3 bucket

## Configuration

Storage type is controlled by the `STORAGE_TYPE` environment variable in your `.env` file.

### Local Storage (Development)

For local development, set:

```env
STORAGE_TYPE=local
LOCAL_BASE_URL=http://localhost:8000
```

Files will be stored in the `uploads/` directory and served via FastAPI's static file serving at `/uploads/`.

**Advantages:**
- No external dependencies
- Fast for development
- Easy to debug
- No additional costs

### S3 Storage (Production)

For production, set:

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
```

**Optional S3 Configuration:**
- `S3_ENDPOINT_URL` - For S3-compatible services (e.g., MinIO)
- `S3_CDN_URL` - CDN URL for serving files (e.g., CloudFront)

**Advantages:**
- Scalable
- Reliable
- Can use CDN for faster delivery
- Better for production environments

## S3 Bucket Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-bucket-name --region us-east-1
```

### 2. Configure Bucket Policy

Your bucket needs to allow public read access for uploaded files. Create a bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

### 3. Configure CORS (if needed)

If your frontend is on a different domain, configure CORS:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

### 4. Create IAM User

Create an IAM user with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name"
    }
  ]
}
```

## Using MinIO (S3-Compatible Storage)

For local S3-compatible storage, you can use MinIO:

1. Install MinIO: https://min.io/download
2. Start MinIO server:
   ```bash
   minio server /data --console-address ":9001"
   ```
3. Configure environment:
   ```env
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=hrms-documents
   S3_REGION=us-east-1
   S3_ENDPOINT_URL=http://localhost:9000
   S3_ACCESS_KEY_ID=minioadmin
   S3_SECRET_ACCESS_KEY=minioadmin
   ```

## Migration from Local to S3

If you need to migrate existing files from local storage to S3:

1. Ensure S3 bucket is configured
2. Set `STORAGE_TYPE=s3` in `.env`
3. Files will be uploaded to S3 going forward
4. Old local files remain in `uploads/` directory but won't be accessible via API

**Note:** To migrate existing files, you would need to write a migration script that:
- Reads files from `uploads/` directory
- Uploads them to S3 using the storage service
- Updates database records with new S3 paths

## File Organization

Files are organized in S3 as:
```
documents/
  {user_id}/
    {user_id}_{document_type}_{uuid}.{ext}
```

Example:
```
documents/
  1/
    1_profile_a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
    1_aadhaar_front_b2c3d4e5-f6g7-8901-bcde-f12345678901.png
```

## Troubleshooting

### Local Storage Issues

- Ensure `uploads/` directory exists and is writable
- Check `LOCAL_BASE_URL` matches your server URL
- Verify file permissions

### S3 Storage Issues

- Verify AWS credentials are correct
- Check bucket name and region
- Ensure bucket policy allows public read access
- Verify IAM user has necessary permissions
- Check network connectivity to AWS

### File Not Found Errors

- For local storage: Check file exists in `uploads/` directory
- For S3: Verify file path in database matches S3 key
- Check file URL generation in `storage.get_file_url()`

## Security Considerations

1. **File Validation**: All files are validated for type and size
2. **Access Control**: File access is controlled by application authentication
3. **S3 Permissions**: Use IAM policies to restrict access
4. **CDN**: Consider using CloudFront for additional security and performance

## Testing

To test storage configuration:

1. **Local Storage**: Upload a file and verify it appears in `uploads/` directory
2. **S3 Storage**: Upload a file and verify it appears in your S3 bucket

Check logs for storage initialization messages:
- `Local file storage enabled` for local storage
- `S3 storage initialized for bucket: {bucket_name}` for S3 storage

