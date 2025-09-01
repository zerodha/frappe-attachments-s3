import os


def load_s3_settings(s3_settings_doc):
    """Load S3 settings from site config or environment variables."""
    if s3_settings_doc.load_credentials_from_env:
        s3_settings = {
            "bucket_url": os.getenv("S3_BUCKET_URL"),
            "bucket_name": os.getenv("S3_BUCKET_NAME"),
            "region_name": os.getenv("S3_REGION_NAME"),
            "aws_key": os.getenv("S3_KEY"),
            "aws_secret": os.getenv("S3_SECRET"),
            "folder_name": os.getenv("S3_FOLDER_NAME"),
            "signed_url_expiry_time": os.getenv("S3_SIGNED_URL_EXPIRY_TIME"),
            "delete_file_from_cloud": os.getenv("S3_DELETE_FILE_FROM_CLOUD"),
        }
    else:
        s3_settings = {
            "bucket_url": s3_settings_doc.bucket_url,
            "bucket_name": s3_settings_doc.bucket_name,
            "region_name": s3_settings_doc.region_name,
            "aws_key": s3_settings_doc.aws_key,
            "aws_secret": s3_settings_doc.aws_secret,
            "folder_name": s3_settings_doc.folder_name,
            "signed_url_expiry_time": s3_settings_doc.signed_url_expiry_time,
            "delete_file_from_cloud": s3_settings_doc.delete_file_from_cloud,
        }
        
    return s3_settings
