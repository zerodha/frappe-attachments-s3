from __future__ import unicode_literals

import datetime
import os
import random
import re
import string

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

import frappe
import magic


class S3Operations(object):

    def __init__(self):
        """
        Function to initialise the aws settings from frappe S3 File attachment
        doctype.
        """
        self.s3_settings_doc = frappe.get_doc(
            'S3 File Attachment',
            'S3 File Attachment',
        )
        if (
            self.s3_settings_doc.aws_key and
            self.s3_settings_doc.aws_secret
        ):
            self.S3_CLIENT = boto3.client(
                's3',
                aws_access_key_id=self.s3_settings_doc.aws_key,
                aws_secret_access_key=self.s3_settings_doc.aws_secret,
                region_name=self.s3_settings_doc.region_name,
                config=Config(signature_version='s3v4')
            )
        else:
            self.S3_CLIENT = boto3.client(
                's3',
                region_name=self.s3_settings_doc.region_name,
                config=Config(signature_version='s3v4')
            )
        self.BUCKET = self.s3_settings_doc.bucket_name
        self.folder_name = self.s3_settings_doc.folder_name

    def strip_special_chars(self, file_name):
        regex = re.compile('[^0-9a-zA-Z._-]')
        file_name = regex.sub('', file_name)
        return file_name

    def key_generator(self, file_name, parent_doctype, parent_name):
        hook_cmd = frappe.get_hooks().get("s3_key_generator")
        if hook_cmd:
            try:
                k = frappe.get_attr(hook_cmd[0])(
                    file_name=file_name,
                    parent_doctype=parent_doctype,
                    parent_name=parent_name
                )
                if k:
                    return k.rstrip('/').lstrip('/')
            except:
                pass

        file_name = file_name.replace(' ', '_')
        file_name = self.strip_special_chars(file_name)
        key = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )

        today = datetime.datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        if self.folder_name:
            return f"{self.folder_name}/{year}/{month}/{day}/{parent_doctype}/{key}_{file_name}"
        return f"{year}/{month}/{day}/{parent_doctype}/{key}_{file_name}"

    def upload_files_to_s3_with_key(
        self, file_path, file_name, is_private, parent_doctype, parent_name
    ):
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
            frappe.throw(frappe._("File Upload Failed. Please try again."))
        return key

    def delete_from_s3(self, key):
        if self.s3_settings_doc.delete_file_from_cloud:
            try:
                self.S3_CLIENT.delete_object(
                    Bucket=self.s3_settings_doc.bucket_name,
                    Key=key
                )
            except ClientError:
                frappe.throw(frappe._("Access denied: Could not delete file"))

    def read_file_from_s3(self, key):
        return self.S3_CLIENT.get_object(Bucket=self.BUCKET, Key=key)

    def get_url(self, key, file_name=None):
        if self.s3_settings_doc.signed_url_expiry_time:
            self.signed_url_expiry_time = self.s3_settings_doc.signed_url_expiry_time
        else:
            self.signed_url_expiry_time = 120

        params = {
            'Bucket': self.BUCKET,
            'Key': key,
        }
        if file_name:
            params['ResponseContentDisposition'] = f'filename={file_name}'

        return self.S3_CLIENT.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=self.signed_url_expiry_time,
        )


@frappe.whitelist()
def file_upload_to_s3(doc, method):
    # Allow callers to explicitly skip S3 upload
    if frappe.local.form_dict.get("skip_s3_upload") in (1, "1", True, "true", "True"):
        return

    path = doc.file_url
    site_path = frappe.utils.get_site_path()
    parent_doctype = doc.attached_to_doctype or 'File'
    parent_name = doc.attached_to_name
    ignore_s3_upload_for_doctype = (
        frappe.local.conf.get('ignore_s3_upload_for_doctype') or ['Data Import']
    )

    if parent_doctype in ignore_s3_upload_for_doctype:
        return

    # Skip if file_url already points to S3 (e.g. CRM comment attachments)
    if path and s3_file_regex_match(path):
        return

    s3_upload = S3Operations()

    if not doc.is_private:
        file_path = site_path + '/public' + path
    else:
        file_path = site_path + path

    # Safety net: skip if local file doesn't exist
    if not os.path.exists(file_path):
        return

    key = s3_upload.upload_files_to_s3_with_key(
        file_path, doc.file_name,
        doc.is_private, parent_doctype,
        parent_name
    )

    if doc.is_private:
        method = "frappe_s3_attachment.controller.generate_file"
        file_url = "/api/method/{0}?key={1}&file_name={2}".format(
            method, key, doc.file_name
        )
    else:
        file_url = '{}/{}/{}'.format(
            s3_upload.S3_CLIENT.meta.endpoint_url,
            s3_upload.BUCKET,
            key
        )

    os.remove(file_path)

    frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
        old_parent=%s, content_hash=%s WHERE name=%s""", (
        file_url, 'Home/Attachments', 'Home/Attachments', key, doc.name))

    doc.file_url = file_url

    if parent_doctype and frappe.get_meta(parent_doctype).get('image_field'):
        frappe.db.set_value(
            parent_doctype,
            parent_name,
            frappe.get_meta(parent_doctype).get('image_field'),
            file_url
        )

    frappe.db.commit()


@frappe.whitelist()
def generate_file(key=None, file_name=None):
    if key:
        s3_upload = S3Operations()
        signed_url = s3_upload.get_url(key, file_name)
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = signed_url
    else:
        frappe.local.response['body'] = "Key not found."
    return


def upload_existing_files_s3(name):
    file_doc_name = frappe.db.get_value('File', {'name': name})
    if file_doc_name:
        doc = frappe.get_doc('File', name)
        s3_upload = S3Operations()
        path = doc.file_url
        site_path = frappe.utils.get_site_path()
        parent_doctype = doc.attached_to_doctype
        parent_name = doc.attached_to_name
        if not doc.is_private:
            file_path = site_path + '/public' + path
        else:
            file_path = site_path + path

        if not os.path.exists(file_path):
            return

        key = s3_upload.upload_files_to_s3_with_key(
            file_path, doc.file_name,
            doc.is_private, parent_doctype,
            parent_name
        )

        if doc.is_private:
            method = "frappe_s3_attachment.controller.generate_file"
            file_url = "/api/method/{0}?key={1}".format(method, key)
        else:
            file_url = '{}/{}/{}'.format(
                s3_upload.S3_CLIENT.meta.endpoint_url,
                s3_upload.BUCKET,
                key
            )

        os.remove(file_path)

        frappe.db.sql(
            """UPDATE `tabFile` SET file_url=%s, folder=%s,
            old_parent=%s, content_hash=%s WHERE name=%s""",
            (file_url, "Home/Attachments", "Home/Attachments", key, doc.name),
        )
        frappe.db.commit()


def s3_file_regex_match(file_url):
    return re.match(
        r'^(https:|/api/method/frappe_s3_attachment.controller.generate_file)',
        file_url
    )


@frappe.whitelist()
def migrate_existing_files():
    files_list = frappe.get_all(
        'File',
        fields=['name', 'file_url']
    )
    for file in files_list:
        if file['file_url']:
            if not s3_file_regex_match(file['file_url']):
                upload_existing_files_s3(file['name'])
    return True


def delete_from_cloud(doc, method):
    s3 = S3Operations()
    s3.delete_from_s3(doc.content_hash)


@frappe.whitelist()
def ping():
    return "pong"
