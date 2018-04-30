import boto3
import botocore
import frappe


class S3Upload(object):
    
    def __init__(self):
        """
        Function to initialise the aws settings from frappe S3 File attachment
        doctype.
        """
        
        self.BUCKET = "zerodha-crm-documents"
        self.folder_name = "acop/uploads/"

    def strip_special_chars(self, file_name):
        """
        Strips file charachters which doesnt match the regex.
        """
        regex = re.compile('[^0-9a-zA-Z]')
        file_name = regex.sub('', file_name)
        return file_name

    def key_generator(self, file_name, parent_doctype, parent_name):
        """
        Generate keys for s3 objects uploaded with file name attached.
        """
        file_name = file_name.replace(' ', '_')
        file_name = self.strip_special_chars(file_name)
        key = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

        today = datetime.datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        doc_path = None
        try:
            doc_path = frappe.db.get_value(
                parent_doctype, {'name': parent_name}, ['s3_folder_path'])
            doc_path = doc_path.rstrip('/').lstrip('/')
        except Exception as e:
            print e

        if not doc_path:
            if self.folder_name:
                final_key = self.folder_name + "/" + year + "/" + month + "/" + \
                    day + "/" + parent_doctype + "/" + key + "_" + file_name
            else:
                final_key = year + "/" + month + "/" + day + "/" + \
                    parent_doctype + "/" + key + "_" + file_name
            return final_key
        else:
            final_key = doc_path + '/' + key + "_" + file_name
            return final_key

    def upload_files_to_s3_with_key(
            self, file_path, file_name, is_private, parent_doctype, parent_name):
        """
        Uploads a new file to S3.
        Strips the file extension to set the content_type in metadata.
        """
        uploaded = True
        file_extension = file_path.split('.')[-1]
        key = self.key_generator(file_name, parent_doctype, parent_name)
        if file_extension.lower() == "pdf":
            content_type = 'application/pdf'
        elif file_extension.lower() == 'png':
            content_type = 'image/png'
        elif file_extension.lower() == 'jpeg':
            content_type = 'image/jpeg'
        elif file_extension.lower() == 'jpg':
            content_type = 'image/jpeg'
        else:
            content_type = 'text/plain'
        try:
            if is_private:
                self.S3_CLIENT.upload_file(
                    file_path, self.BUCKET, key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": {
                            "ContentType": content_type,
                            "file_name": file_name
                        }
                    }
                )
            else:
                self.S3_CLIENT.upload_file(
                    file_path, self.BUCKET, key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "ACL": 'public-read',
                        "Metadata": {
                            "ContentType": content_type,

                        }
                    }
                )

        except boto3.exceptions.S3UploadFailedError:
            uploaded = False
        return key, uploaded

    def read_file_from_s3(self, key):
        """
        Function to read file from a s3 file.
        """
        downloaded = True
        try:
            bucket = self.S3.Bucket(self.BUCKET)
            file_obj = bucket.Object(key)
            return file_obj
        except botocore.exceptions.ClientError:
            downloaded = False
        return downloaded



response = Response()
    s3_upload = S3Upload()
    response.headers["Content-Disposition"] = 'inline; filename=%s' % key
    file_obj = s3_upload.read_file_from_s3(key)
    if file_obj:
        response.data = file_obj.get()['Body'].read()
        response.headers['Content-Type'] = file_obj.metadata['contenttype']
        return response
