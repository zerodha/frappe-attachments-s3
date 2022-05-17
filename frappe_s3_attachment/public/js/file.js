frappe.ui.form.on('File', {
	refresh(frm) {
		// your code here
    	if(frm.doc.file_name && frm.doc.file_name.split('.').splice(-1)[0]==='zip') {
    		frm.add_custom_button(__('Unzip S3'), function() {
    			frappe.call({
    				method: "frappe_s3_attachment.events.file.unzip_file_s3",
    				args: {
    					name: frm.doc.name,
    				},
    				freeze: true,
    				freeze:'Processing ...',
    				callback: function() {
    					frappe.set_route('List', 'File');
    				}
    			});
    		});
    	}
	}
})