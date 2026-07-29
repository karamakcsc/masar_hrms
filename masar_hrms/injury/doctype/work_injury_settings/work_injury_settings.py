# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WorkInjurySettings(Document):
	pass


def get_settings():
	return frappe.get_cached_doc("Work Injury Settings")
