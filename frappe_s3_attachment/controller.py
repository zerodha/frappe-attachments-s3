from __future__ import unicode_literals

import os
import random
import string
import urllib
import datetime
import re

import boto3
import magic
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
        self.S3 = boto3.resource('s3', region_name=s3_settings_doc.region_name)
        self.S3_CLIENT = boto3.client(
            's3',
            aws_access_key_id=s3_settings_doc.aws_key,
            aws_secret_access_key=s3_settings_doc.aws_secret,
            region_name=s3_settings_doc.region_name,
        )
        self.BUCKET = s3_settings_doc.bucket_name
        self.folder_name = s3_settings_doc.folder_name

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
        mime_type = magic.from_file(file_path, mime=True)
        key = self.key_generator(file_name, parent_doctype, parent_name)
        content_type = mime_type
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
            file_obj = self.S3_CLIENT.get_object(Bucket=self.BUCKET, Key=key)
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
    parent_doctype = doc.attached_to_doctype
    parent_name = doc.attached_to_name
    if not doc.is_private:
        file_path = site_path + '/public' + path
    else:
        file_path = site_path + path
    key, status = s3_upload.upload_files_to_s3_with_key(
        file_path, doc.file_name, doc.is_private, parent_doctype, parent_name)
    if status:
        if doc.is_private:
            file_url = "/api/method/frappe_s3_attachment.controller.generate_file?key=%s" % key
        else:
            file_url = '{}/{}/{}'.format(
                s3_upload.S3_CLIENT.meta.endpoint_url,
                s3_upload.BUCKET,
                key
            )
        # os.remove(file_path)
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
            print dir(file_obj)
            response.data = file_obj['Body'].read()
            response.headers['Content-Type'] = file_obj['ContentType']
            return response
        else:
            response.data = "File not found."
            return response
    else:
        response.data = "Key not found."
        return response


def upload_existing_files_s3(name, file_name):
    """
    Function to upload all existing files.
    """
    file_doc_name = frappe.db.get_value('File', {'name': name})
    if file_doc_name:
        doc = frappe.get_doc('File', name)
        s3_upload = S3Upload()
        path = doc.file_url
        site_path = frappe.utils.get_site_path()
        parent_doctype = doc.attached_to_doctype
        parent_name = doc.attached_to_name
        if not doc.is_private:
            file_path = site_path + '/public' + path
        else:
            file_path = site_path + path
        key, status = s3_upload.upload_files_to_s3_with_key(
            file_path, doc.file_name, doc.is_private, parent_doctype, parent_name)
        if status:
            if doc.is_private:
                file_url = "/api/method/frappe_s3_attachment.controller.generate_file?key=%s" % key
            else:
                file_url = '{}/{}/{}'.format(
                    s3_upload.S3_CLIENT.meta.endpoint_url,
                    s3_upload.BUCKET,
                    key
                )
            # os.remove(file_path)
            doc = frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
                old_parent=%s, content_hash=%s WHERE name=%s""", (
                file_url, 'Home/Attachments', 'Home/Attachments', key, doc.name))
            frappe.db.commit()
    else:
        pass


def s3_file_regex_match(file_url):
    """
    Match the public file regex match.
    """
    return re.match(r'^(https:|/api/method/frappe_s3_attachment.controller.generate_file)', file_url)


@frappe.whitelist()
def migrate_existing_files():
    """
    Function to migrate the existing files to s3.
    """
    # get_all_files_from_public_folder_and_upload_to_s3
    site_path = frappe.utils.get_site_path()
    file_path = site_path + '/public/files/'
    files_list = frappe.get_all(
        'File', fields=['name', 'file_url', 'file_name'])
    for file in files_list:
        if file['file_url']:
            try:
                if not s3_file_regex_match(file['file_url']):
                    print file['file_url'], file['file_name'], file['name']
                    upload_existing_files_s3(file['name'], file['file_name'])
            except Exception as e:
                print e
    return True



def delete_from_cloud(doc, method):
    """Delete file from s3"""
    from botocore.exceptions import ClientError

    s3_settings_doc = frappe.get_doc(
            'S3 File Attachment',
            'S3 File Attachment',
        )

    S3 = boto3.resource('s3', region_name=s3_settings_doc.region_name)
    S3_CLIENT = boto3.client(
        's3',
        aws_access_key_id=s3_settings_doc.aws_key,
        aws_secret_access_key=s3_settings_doc.aws_secret,
        region_name=s3_settings_doc.region_name,
    )
    BUCKET = s3_settings_doc.bucket_name


    try:
        S3_CLIENT.delete_object(
            Bucket=s3_settings_doc.bucket_name,
            Key=doc.content_hash
        )
    except ClientError as e:
        frappe.throw("Access denied")


@frappe.whitelist()
def ping():
    """
    Test function to check if api function work.
    """
    return "pong"
