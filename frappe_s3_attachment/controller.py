from __future__ import unicode_literals

import os
import random
import string
import urllib

import boto3
import botocore
import frappe

from werkzeug.wrappers import Response


# Globals


class s3Upload(object):
    
    def __init__(self):
        s3_settings_doc = frappe.get_doc('S3 Attachment Settings', 's3')
        self.S3 = boto3.resource('s3')
        self.S3_CLIENT = boto3.client(
            's3',
            aws_access_key_id=s3_settings_doc.aws_key,
            aws_secret_access_key=s3_settings_doc.aws_secret,
        )
        self.BUCKET = s3_settings_doc.bucket_name
        self.folder_name = s3_settings_doc.folder_name

    def key_generator(self, file_name):
        """
        Generate keys for s3 objects uploaded with file name attached.
        """
        file_name = file_name.replace(' ', '_')
        key = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        if self.folder_name:
            final_key = self.folder_name + "/" + key + "_" + file_name
        else:
            final_key = key + "_" + file_name
        return final_key

    def upload_files_to_s3_with_key(self, file_path, file_name):
        """
        Uploads a new file to S3.
        Strips the file extension to set the content_type in metadata.
        """
        uploaded = True
        file_extension = file_path.split('.')[-1]
        key = self.key_generator(file_name)
        if file_extension == "pdf":
            content_type = 'application/pdf'
        else:
            content_type = 'text/plain'
        try:
            self.S3_CLIENT.upload_file(
                file_path, self.BUCKET, key,
                ExtraArgs={"Metadata": {
                    "ContentType": content_type
                }}
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


@frappe.whitelist()
def file_upload_to_s3(doc, method):
    """
    check and upload files to s3. the path check and
    """
    s3_upload = s3Upload()
    path = doc.file_url
    site_path = frappe.utils.get_site_path()
    if not doc.is_private:    
        file_path = site_path + '/public' + path
    else:
        file_path = site_path + path
    key, status = s3_upload.upload_files_to_s3_with_key(
        file_path, doc.file_name)
    if status:
        file_url = "/api/method/frappe_s3_attachment.controller.generate_file?key=%s" % key
        os.remove(file_path)
        doc = frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
            old_parent=%s, content_hash=%s WHERE name=%s""", (
            file_url, 'Home/Attachments', 'Home/Attachments', None, doc.name))
        frappe.db.commit()
    else:
        frappe.throw('File upload failed, Please try again.')


@frappe.whitelist()
def generate_file(key=None):
    """
    Function to stream file from s3.
    """
    if key:
        response = Response()
        s3_upload = s3Upload()
        response.headers["Content-Disposition"] = 'inline; filename=%s' % key
        file_obj = s3_upload.read_file_from_s3(key)
        if file_obj:
            response.data = file_obj.get()['Body'].read()
            response.headers['Content-Type'] = file_obj.metadata['contenttype']
            return response
        else:
            frappe.throw('File not found. Please try again.')
    else:
        frappe.throw('File not found. Please try again.')


@frappe.whitelist()
def ping():
    """
    Test function to check if api function work.
    """
    return "pong"