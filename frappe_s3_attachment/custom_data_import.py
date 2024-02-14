import frappe
from frappe import _
from frappe.utils.background_jobs import enqueue
from frappe.core.doctype.data_import.importer import Importer, get_id_field, get_diff

class CustomImporter(Importer):
    @staticmethod
    def check_and_upload_to_s3(url_path):
        from .controller import public_file_regex_match, erp_or_s3_file_regex_match, gdrive_file_regex_match, S3Operations
        s3_settings_doc = frappe.get_doc(
            'S3 File Attachment',
            'S3 File Attachment',
        )
        if public_file_regex_match(url_path):
            if erp_or_s3_file_regex_match(s3_settings_doc.bucket_name, url_path):
                return url_path
            elif gdrive_file_regex_match(url_path):
                file_doc = frappe.get_doc(
                    {
                        "doctype": "File",
                        "file_url": url_path,
                        "is_private": 0,
                    }
                ).save(ignore_permissions=True)
                return file_doc.file_url
            else:
                frappe.throw(_("File upload from public links disabled"))
        else:
            frappe.throw(_("Only links accepted in data importer for attach fields"))

    def insert_record(self, doc):
        meta = frappe.get_meta(self.doctype)
        new_doc = frappe.new_doc(self.doctype)
        new_doc.update(doc)
        attach_fields = [x.fieldname for x in meta.fields if x.fieldtype == 'Attach']
        for attach_field in attach_fields:
            url_path = getattr(new_doc, attach_field, None)
            if url_path:
                setattr(new_doc, attach_field, CustomImporter.check_and_upload_to_s3(url_path))

        if not doc.name and (meta.autoname or "").lower() != "prompt":
            # name can only be set directly if autoname is prompt
            new_doc.set("name", None)

        new_doc.flags.updater_reference = {
            "doctype": self.data_import.doctype,
            "docname": self.data_import.name,
            "label": _("via Data Import"),
        }

        new_doc.insert()
        if meta.is_submittable and self.data_import.submit_after_import:
            new_doc.submit()
        return new_doc
    
    def update_record(self, doc):
        id_field = get_id_field(self.doctype)
        existing_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))

        updated_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))

        updated_doc.update(doc)

        attach_fields = [x.fieldname for x in frappe.get_meta(self.doctype).fields if x.fieldtype == 'Attach']
        for attach_field in attach_fields:
            url_path = getattr(updated_doc, attach_field, None)
            if url_path:
                setattr(updated_doc, attach_field, CustomImporter.check_and_upload_to_s3(url_path))

        if get_diff(existing_doc, updated_doc):
            # update doc if there are changes
            updated_doc.flags.updater_reference = {
                "doctype": self.data_import.doctype,
                "docname": self.data_import.name,
                "label": _("via Data Import"),
            }
            updated_doc.save()
            return updated_doc
        else:
            # throw if no changes
            frappe.throw(_("No changes to update"))


def start_import(data_import):
    """This method runs in background job"""
    data_import = frappe.get_doc("Data Import", data_import)
    try:
        i = CustomImporter(data_import.reference_doctype, data_import=data_import)
        i.import_data()
    except Exception:
        frappe.db.rollback()
        data_import.db_set("status", "Error")
        data_import.log_error("Data import failed")
    finally:
        frappe.flags.in_import = False

    frappe.publish_realtime("data_import_refresh", {"data_import": data_import.name})


@frappe.whitelist()
def custom_start_import(data_import):
    from frappe.core.page.background_jobs.background_jobs import get_info
    from frappe.utils.scheduler import is_scheduler_inactive

    doc = frappe.get_doc("Data Import", data_import)

    if is_scheduler_inactive() and not frappe.flags.in_test:
        frappe.throw(_("Scheduler is inactive. Cannot import data."), title=_("Scheduler Inactive"))

    enqueued_jobs = [d.get("job_name") for d in get_info()]

    if doc.name not in enqueued_jobs:
        enqueue(
            start_import,
            queue="default",
            timeout=10000,
            event="data_import",
            job_name=doc.name,
            data_import=doc.name,
            now=frappe.conf.developer_mode or frappe.flags.in_test,
        )
        return True

    return False
