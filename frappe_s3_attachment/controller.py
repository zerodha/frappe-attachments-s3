from __future__ import unicode_literals

import datetime
import os
import random
import re
import string
import urllib.parse

import boto3

from botocore.client import Config
from botocore.exceptions import ClientError

import frappe
from frappe.core.doctype.file.file import File

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
        """
        Strips file charachters which doesnt match the regex.
        """
        regex = re.compile('[^0-9a-zA-Z._-]')
        file_name = regex.sub('', file_name)
        return file_name

    def key_generator(self, file_name, parent_doctype, parent_name):
        """
        Generate keys for s3 objects uploaded with file name attached.
        """
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
            random.choice(
                string.ascii_uppercase + string.digits) for _ in range(8)
        )

        today = datetime.datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        doc_path = None

        if not doc_path:
            if self.folder_name:
                final_key = self.folder_name + "/" + year + "/" + month + \
                    "/" + day + "/" + parent_doctype + "/" + key + "_" + \
                    file_name
            else:
                final_key = year + "/" + month + "/" + day + "/" + \
                    parent_doctype + "/" + key + "_" + file_name
            return final_key
        else:
            final_key = doc_path + '/' + key + "_" + file_name
            return final_key

    def upload_files_to_s3_with_key(
            self, file_path, file_name, is_private, parent_doctype, parent_name
    ):
        """
        Uploads a new file to S3.
        Strips the file extension to set the content_type in metadata.
        """
        mime_type = magic.from_file(file_path, mime=True)
        key = self.key_generator(file_name, parent_doctype, parent_name)
        content_type = mime_type
        ascii_file_name = file_name.encode('ascii', 'ignore').decode('ascii')
        try:
            if is_private:
                self.S3_CLIENT.upload_file(
                    file_path, self.BUCKET, key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": {
                            "ContentType": content_type,
                            "file_name": ascii_file_name
                        }
                    }
                )
            else:
                self.S3_CLIENT.upload_file(
                    file_path, self.BUCKET, key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": {
                            "ContentType": content_type,
                        }
                    }
                )

        except boto3.exceptions.S3UploadFailedError:
            frappe.throw(frappe._("File Upload Failed. Please try again."))
        return key

    def delete_from_s3(self, key):
        """ Delete file from s3"""
        if self.s3_settings_doc.delete_file_from_cloud:
            try:
                self.S3_CLIENT.delete_object(
                    Bucket=self.s3_settings_doc.bucket_name,
                    Key=key
                )
            except ClientError:
                frappe.throw(frappe._("Access denied: Could not delete file"))

    def read_file_from_s3(self, key):
        """
        Function to read file from a s3 file.
        """
        return self.S3_CLIENT.get_object(Bucket=self.BUCKET, Key=key)

    def get_url(self, key, file_name=None):
        """
        Return url.

        :param bucket: s3 bucket name
        :param key: s3 object key
        """
        if self.s3_settings_doc.signed_url_expiry_time:
            self.signed_url_expiry_time = self.s3_settings_doc.signed_url_expiry_time # noqa
        else:
            self.signed_url_expiry_time = 120
        params = {
                'Bucket': self.BUCKET,
                'Key': key,

        }
        if file_name:
            params['ResponseContentDisposition'] = 'filename={}'.format(file_name)

        url = self.S3_CLIENT.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=self.signed_url_expiry_time,
        )

        return url


@frappe.whitelist()
def file_upload_to_s3(doc, method):
    """
    check and upload files to s3. the path check and
    """
    s3_upload = S3Operations()
    path = doc.file_url
    site_path = frappe.utils.get_site_path()
    parent_doctype = doc.attached_to_doctype or 'File'
    parent_name = doc.attached_to_name
    ignore_s3_upload_for_doctype = frappe.local.conf.get('ignore_s3_upload_for_doctype', [])
    if parent_doctype not in ignore_s3_upload_for_doctype:
        if not doc.is_private:
            file_path = site_path + '/public' + path
        else:
            file_path = site_path + path
        key = s3_upload.upload_files_to_s3_with_key(
            file_path, doc.file_name,
            doc.is_private, parent_doctype,
            parent_name
        )

        generate_method = "frappe_s3_attachment.controller.generate_file"
        file_url = """/api/method/{0}?key={1}&file_name={2}""".format(
            generate_method, key, urllib.parse.quote(doc.file_name)
        )

        frappe.db.sql("""UPDATE `tabFile` SET file_url=%s, folder=%s,
            old_parent=%s WHERE name=%s""", (
            file_url, 'Home/Attachments', 'Home/Attachments', doc.name))

        doc.file_url = file_url

        if parent_doctype and frappe.get_meta(parent_doctype).get('image_field'):
            frappe.db.set_value(parent_doctype, parent_name, frappe.get_meta(parent_doctype).get('image_field'), file_url)

        frappe.db.commit()

        # Remove local file only after DB commit succeeds
        os.remove(file_path)


@frappe.whitelist()
def generate_file(key=None, file_name=None):
    """
    Function to stream file from s3.
    """
    if key:
        s3_upload = S3Operations()
        signed_url = s3_upload.get_url(key, file_name)
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = signed_url
    else:
        frappe.local.response['body'] = "Key not found."
    return


def upload_existing_files_s3(name):
    """
    Function to upload all existing files.
    """
    file_doc_name = frappe.db.get_value('File', {'name': name})
    if file_doc_name:
        doc = frappe.get_doc('File', name)
        s3_upload = S3Operations()
        path = doc.file_url
        site_path = frappe.utils.get_site_path()
        parent_doctype = doc.attached_to_doctype or 'File'
        parent_name = doc.attached_to_name
        if not doc.is_private:
            file_path = site_path + '/public' + path
        else:
            file_path = site_path + path

        # File exists?
        if not os.path.exists(file_path):
            return

        key = s3_upload.upload_files_to_s3_with_key(
            file_path, doc.file_name,
            doc.is_private, parent_doctype,
            parent_name
        )

        generate_method = "frappe_s3_attachment.controller.generate_file"
        file_url = """/api/method/{0}?key={1}&file_name={2}""".format(
            generate_method, key, urllib.parse.quote(doc.file_name)
        )

        frappe.db.sql(
            """UPDATE `tabFile` SET file_url=%s, folder=%s,
            old_parent=%s WHERE name=%s""",
            (file_url, "Home/Attachments", "Home/Attachments", doc.name),
        )
        frappe.db.commit()

        # Remove local file only after DB commit succeeds
        os.remove(file_path)


def s3_file_regex_match(file_url):
    """
    Match the public file regex match.
    """
    return re.match(
        r'^(https:|/api/method/frappe_s3_attachment.controller.generate_file)',
        file_url
    )


@frappe.whitelist()
def migrate_existing_files():
    """
    Enqueue a background job to migrate all local files to S3.
    Returns immediately so the HTTP request does not time out.
    """
    frappe.enqueue(
        "frappe_s3_attachment.controller._migrate_files_background",
        queue="long",
        timeout=18000,
        job_name="S3 Migration",
    )
    return "Migration started in background. Check Error Log for any failures."


def _migrate_files_background():
    """
    Fetch all non-S3 file names and enqueue them in batches of 500.
    """
    BATCH_SIZE = 500

    all_files = frappe.db.get_all(
        "File",
        filters=[["file_url", "not like", "%/api/method/frappe_s3_attachment%"],
                 ["file_url", "not like", "https:%"],
                 ["file_url", "!=", ""]],
        fields=["name"],
        pluck="name",
    )

    for i in range(0, len(all_files), BATCH_SIZE):
        batch = all_files[i: i + BATCH_SIZE]
        frappe.enqueue(
            "frappe_s3_attachment.controller._migrate_batch",
            queue="long",
            timeout=3600,
            job_name="S3 Migration batch {}-{}".format(i, i + len(batch)),
            file_names=batch,
        )


def _migrate_batch(file_names):
    """
    Migrate a batch of files to S3. Failures are logged per-file and do not
    stop the rest of the batch.
    """
    for name in file_names:
        try:
            file_url = frappe.db.get_value("File", name, "file_url")
            if not file_url or s3_file_regex_match(file_url):
                continue
            upload_existing_files_s3(name)
        except Exception:
            frappe.log_error(
                title="S3 Migration failed for file: {}".format(name),
                message=frappe.get_traceback(),
            )


def delete_from_cloud(doc, method):
    """Delete file from s3"""
    if not doc.file_url or not s3_file_regex_match(doc.file_url):
        return
    parsed = urllib.parse.urlparse(doc.file_url)
    key = urllib.parse.parse_qs(parsed.query).get("key", [None])[0]
    if not key:
        key = doc.content_hash
    if key:
        s3 = S3Operations()
        s3.delete_from_s3(key)


@frappe.whitelist()
def ping():
    """
    Test function to check if api function work.
    """
    return "pong"


class CustomFile(File):
    """Extends Frappe's File doctype to support content retrieval for files stored in S3
    via the frappe_s3_attachment URL pattern (/api/method/frappe_s3_attachment.controller.generate_file?key=...)."""

    def get_content(self) -> bytes:
        if self.file_url and s3_file_regex_match(self.file_url):
            parsed = urllib.parse.urlparse(self.file_url)
            params = urllib.parse.parse_qs(parsed.query)
            key = params.get("key", [None])[0]
            if key:
                s3 = S3Operations()
                response = s3.read_file_from_s3(key)
                return response["Body"].read()
        return super().get_content()
