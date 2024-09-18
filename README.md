<a href="https://zerodha.tech"><img src="https://zerodha.tech/static/images/github-badge.svg" align="right" /></a>

## Frappe S3 Attachment

Frappe app to make file upload automatically upload and read from s3.

#### Features.

1. Upload both public and private files to s3.
2. Stream files from S3, when file is viewed everytime.
3. Lets you add S3 credentials
    (aws key, aws secret, bucket name, folder name) through ui and migrate existing
    files.
4. Deletes from s3 whenever a file is deleted in ui.
5. Files are uploaded categorically in the format.
    {s3_folder_path}/{year}/{month}/{day}/{doctype}/{file_hash}

#### Installation.

1. bench get-app https://github.com/zerodhatech/Frappe-attachments-s3.git
2. bench install-app frappe_s3_attachment

#### Configuration Setup.

1. Open single doctype "s3 File Attachment"
2. Enter (Bucket Name, AWS key, AWS secret, S3 bucket Region name, Folder Name)
    Folder Name- folder name is the default folder path in s3.
3. Migrate existing files lets all the existing files in private and public folders
    to be migrated to s3.
4. Delete From Cloud when selected deletes the file form s3 bucket whenever a file
    is deleted from ui. By default the Delete from cloud will be unchecked.

### AWS Policies for Successful Configuration

To successfully upload and serve images to/from the S3 bucket, use the following policies:

#### S3 Bucket Policy

Replace the placeholders with your AWS Account ID and Bucket Name.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<AWS_ACCOUNT_ID>:user/<YOUR_IAM_USER>"
            },
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::<YOUR_BUCKET_NAME>",
                "arn:aws:s3:::<YOUR_BUCKET_NAME>/*"
            ]
        }
    ]
}
```
#### IAM Policy
Attach this policy to your IAM user or role that Frappe uses to interact with S3:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::<YOUR_BUCKET_NAME>",
                "arn:aws:s3:::<YOUR_BUCKET_NAME>/*"
            ]
        }
    ]
}
```
#### CORS Policy
Set this CORS configuration for your S3 bucket to allow access from your Frappe application:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
        "AllowedOrigins": ["https://<YOUR_FRAPPE_APPLICATION_DOMAIN>"],
        "ExposeHeaders": ["ETag", "x-amz-meta-custom-header"],
        "MaxAgeSeconds": 3000
    }
]
```


### Explanation of the Combined Policies

1. **S3 Bucket Policy**:
   - Combines all necessary actions (`s3:GetBucketLocation`, `s3:ListBucket`, `s3:GetObject`) into a single policy statement for simplicity.
   - Specifies the principal (IAM user or role) that needs these permissions.
   - Applies the actions to both the bucket itself (`arn:aws:s3:::<YOUR_BUCKET_NAME>`) and all objects within the bucket (`arn:aws:s3:::<YOUR_BUCKET_NAME>/*`).

2. **IAM Policy**:
   - Provides full S3 access (`s3:*`) to the specified bucket and its objects.
   - Attach this policy to the IAM user or role that the Frappe app uses to manage S3.

3. **CORS Policy**:
   - Ensures that your Frappe application can interact with S3 by allowing necessary HTTP methods and headers for cross-origin requests.

### Usage

Replace placeholders with actual values:
- **`<AWS_ACCOUNT_ID>`**: Your AWS Account ID.
- **`<YOUR_IAM_USER>`**: The IAM user or role for the Frappe application.
- **`<YOUR_BUCKET_NAME>`**: Your S3 bucket name.
- **`<YOUR_FRAPPE_APPLICATION_DOMAIN>`**: The domain of your Frappe application.

By using these policies, you ensure that your Frappe app can successfully upload, read, and manage files in your S3 bucket.

#### License

MIT
