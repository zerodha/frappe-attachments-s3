## Frappe S3 Attachment

Frappe app to make file upload to S3 through attach file option in doctype.

#### Features.

1. Upload both public and private files to s3.
2. Stream files from S3, when you view the file everytime.
3. Lets you add S3 credentials and config 
    (aws key, aws secret, bucket name, folder name) through ui.

#### Initial Setup.
- `bench get-app git@github.com:zerodhatech/Frappe-attachments-s3.git`
- `bench install-app frappe_s3_attachment`
- `pip install -r apps/frappe_s3_attachment/requirements.txt`
- Setup aws initial configuration in ui from `S3 Attachment Settings` Doctype.

#### License

MIT
