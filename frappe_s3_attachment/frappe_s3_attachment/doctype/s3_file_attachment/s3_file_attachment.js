// Copyright (c) 2018, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('S3 File Attachment', {
	refresh: function(frm) {

	},
	migrate_existing_files: function (frm) {
        frappe.call({
            method: "frappe_s3_attachment.controller.migrate_existing_files",
            callback: function (data) {
                if (data.message) {
                    frappe.msgprint(
                        data.message + "<br><br>Monitor progress in <b>Error Log</b> for any per-file failures.",
                        "S3 Migration"
                    );
                } else {
                    frappe.msgprint('Failed to start migration. Check Error Log.', 'S3 Migration');
                }
            }
        });
    },
});
