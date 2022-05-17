import frappe
import zipfile
import os
from frappe import _
from frappe_s3_attachment.controller import generate_signed_url
import requests


@frappe.whitelist()
def unzip_file_s3(name):
	'''Unzip the given file and make file records for each of the extracted files'''
	file_obj = frappe.get_doc('File', name)
	files = unzip(file_obj)
	return files


def unzip(self):
    '''Unzip current file and replace it by its children'''
    if not self.file_url.endswith(".zip"):
        frappe.throw(_("{0} is not a zip file").format(self.file_name))

    
    s3_zip_path = generate_signed_url(self.content_hash,self.file_name)
    results = requests.get(s3_zip_path)
    with open('/tmp/{0}'.format(self.file_name), 'wb') as f:
        f.write(results.content)
    zip_path = '/tmp/{0}'.format(self.file_name)
    files = []
    with zipfile.ZipFile(zip_path) as z:
        for file in z.filelist:
            if file.is_dir() or file.filename.startswith('__MACOSX/'):
                # skip directories and macos hidden directory
                continue

            filename = os.path.basename(file.filename)
            if filename.startswith('.'):
                # skip hidden files
                continue

            file_doc = frappe.new_doc('File')
            file_doc.content = z.read(file.filename)
            file_doc.file_name = filename
            file_doc.folder = self.folder
            file_doc.is_private = self.is_private
            file_doc.attached_to_doctype = self.attached_to_doctype
            file_doc.attached_to_name = self.attached_to_name
            file_doc.save()
            files.append(file_doc)

    frappe.delete_doc('File', self.name)
    return files