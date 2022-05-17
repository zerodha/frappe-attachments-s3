# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


__version__ = "0.0.1"

old_get_hooks = frappe.get_hooks


def get_hooks(*args, **kwargs):
	if "frappe_s3_attachment" in frappe.get_installed_apps():
		import frappe_s3_attachment.monkey_patches

	return old_get_hooks(*args, **kwargs)


frappe.get_hooks = get_hooks

