# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "frappe_s3_attachment"
app_title = "Frappe S3 Attachment"
app_publisher = "Frappe"
app_description = "Frappe app to make file upload to S3 through attach file option."
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "ramesh.ravi@zerodha.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frappe_s3_attachment/css/frappe_s3_attachment.css"
# app_include_js = "/assets/frappe_s3_attachment/js/frappe_s3_attachment.js"

# include js, css files in header of web template
# web_include_css = "/assets/frappe_s3_attachment/css/frappe_s3_attachment.css"
# web_include_js = "/assets/frappe_s3_attachment/js/frappe_s3_attachment.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_list_js = {
    "S3 Attachment Settings": ["frappe_s3_attachment/doctype/s3_attachment_settings/s3_attachment_settings.js"]
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "frappe_s3_attachment.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "frappe_s3_attachment.install.before_install"
# after_install = "frappe_s3_attachment.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappe_s3_attachment.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
    "File": {
        "after_insert": "frappe_s3_attachment.controller.file_upload_to_s3",
        "on_trash": "frappe_s3_attachment.controller.delete_from_cloud"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappe_s3_attachment.tasks.all"
# 	],
# 	"daily": [
# 		"frappe_s3_attachment.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappe_s3_attachment.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappe_s3_attachment.tasks.weekly"
# 	]
# 	"monthly": [
# 		"frappe_s3_attachment.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "frappe_s3_attachment.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappe_s3_attachment.event.get_events"
# }

