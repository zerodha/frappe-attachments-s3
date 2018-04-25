# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe import _
from frappe.model.document import Document

class AttachmentSettings(Document):

    def validate(self):
        """Validation"""
        self.is_single_integration()

    def is_single_integration(self):

        checkbox = [self.enable_dropbox, self.enable_aws_s3,self. enable_google_drive]
        is_checked = False

        for checkbox_enabled in checkbox:
            if is_checked and checkbox_enabled:
                frappe.throw(_("Only one attachment integration can be enabled"))
            elif checkbox_enabled:
                is_checked = True
            else:
                pass

        if not is_checked:
            frappe.throw(_("One attachment integration is mandatory"))
