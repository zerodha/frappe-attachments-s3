import frappe



def s3_settings():
    return frappe.get_doc("S3 Settings")