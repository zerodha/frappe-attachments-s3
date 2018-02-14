from __future__ import unicode_literals

import os
import random
import string
import urllib
import datetime

import boto3
import botocore
import frappe

from werkzeug.wrappers import Response


# Globals


class S3Upload(object):

    def __init__(self):
        """
        Function to initialise the aws settings from frappe S3 File attachment
        doctype.
        """
        s3_settings_doc = frappe.get_doc(
            'S3 File Attachment',
            'S3 File Attachment',
        )
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
        
        today = datetime.datetime.now()
        year = today.strftime("%Y")
        month=today.strftime("%m")
        day=today.strftime("%d")

        if self.folder_name:
            final_key = year + "/" + month + "/" + day + "/" + self.folder_name + "/" + key + "_" + file_name
        else:
            final_key = year + "/" + month + "/" + day + "/" + key + "_" + file_name
        return final_key

    def upload_files_to_s3_with_key(self, file_path, file_name, is_private):
        """
        Uploads a new file to S3.
        Strips the file extension to set the content_type in metadata.
        """
        uploaded = True
        file_extension = file_path.split('.')[-1]
        key = self.key_generator(file_name)
        if file_extension.lower() == "pdf":
            content_type = 'application/pdf'
        else:
            content_type = 'text/plain'
        try:
            if is_private:
                self.S3_CLIENT.upload_file(
                    file_path, self.BUCKET, key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": {
                            "ContentType": content_type
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


@frappe.whitelist()
def file_upload_to_s3(doc, method):
    """
    check and upload files to s3. the path check and
    """
    s3_upload = S3Upload()
    path = doc.file_url
    site_path = frappe.utils.get_site_path()
    if not doc.is_private:
        file_path = site_path + '/public' + path
    else:
        file_path = site_path + path
    key, status = s3_upload.upload_files_to_s3_with_key(
        file_path, doc.file_name, doc.is_private)
    if status:
        if doc.is_private:
            file_url = "/api/method/frappe_s3_attachment.controller.generate_file?key=%s" % key
        else:
            file_url = '{}/{}/{}'.format(
                s3_upload.S3_CLIENT.meta.endpoint_url,
                s3_upload.BUCKET,
                key
            )
        os.remove(file_path)
        doc = frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
            old_parent=%s, content_hash=%s WHERE name=%s""", (
            file_url, 'Home/Attachments', 'Home/Attachments', key, doc.name))
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
        s3_upload = S3Upload()
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


def upload_existing_files_s3(file_name):
    """
    Function to upload all existing files.
    """
    file_doc_name = frappe.db.get_value('File', {'file_name': file_name})
    if file_doc_name:
        doc = frappe.get_doc('File', file_doc_name)
        s3_upload = S3Upload()
        path = doc.file_url
        site_path = frappe.utils.get_site_path()
        if not doc.is_private:
            file_path = site_path + '/public' + path
        else:
            file_path = site_path + path
        key, status = s3_upload.upload_files_to_s3_with_key(
            file_path, doc.file_name, doc.is_private)
        if status:
            if doc.is_private:
                file_url = "/api/method/frappe_s3_attachment.controller.generate_file?key=%s" % key
            else:
                file_url = '{}/{}/{}'.format(
                    s3_upload.S3_CLIENT.meta.endpoint_url,
                    s3_upload.BUCKET,
                    key
                )
            os.remove(file_path)
            doc = frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
                old_parent=%s, content_hash=%s WHERE name=%s""", (
                file_url, 'Home/Attachments', 'Home/Attachments', key, doc.name))
            frappe.db.commit()
    else:
        pass


@frappe.whitelist()
def migrate_existing_files(user):
    """
    Function to migrate the existing files to s3.
    """
    # get_all_files_from_public_folder_and_upload_to_s3
    site_path = frappe.utils.get_site_path()
    file_path = site_path + '/public/files/'
    # else:
    #     file_path = site_path + '/private/files/'
    for file_name in os.listdir(file_path):
        upload_existing_files_s3(file_name)
    file_path = site_path + '/private/files/'
    for file_name in os.listdir(file_path):
        upload_existing_files_s3(file_name)
    return True


@frappe.whitelist()
def ping():
    """
    Test function to check if api function work.
    """
    return "pong"
