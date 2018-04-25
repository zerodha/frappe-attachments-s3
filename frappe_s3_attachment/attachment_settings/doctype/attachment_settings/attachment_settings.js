// Copyright (c) 2018, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attachment Settings', {
	refresh: function(frm) {

	},
    enable_aws_s3: function(frm){
        if(frm.doc.enable_aws_s3 == 1){
            frm.set_value('enable_dropbox', 0);
            frm.set_value('enable_google_drive', 0);
        }
    },
    enable_dropbox: function(frm){
        if(frm.doc.enable_dropbox == 1){
            frm.set_value('enable_aws_s3', 0);
            frm.set_value('enable_google_drive', 0);
        }
    },
    enable_google_drive: function(frm){
        if(frm.doc.enable_google_drive == 1){
            frm.set_value('enable_aws_s3', 0);
            frm.set_value('enable_dropbox', 0);
        }
    }
});
