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

#### License

MIT
