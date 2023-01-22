# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
#
# class EmployeeSocialSecuritySalaryTool(Document):
# 	pass


import frappe
import erpnext, json
from frappe import _, scrub, ValidationError
from frappe.utils import flt, comma_or, nowdate, getdate
import datetime

from frappe.model.document import Document

class EmployeeSocialSecuritySalaryTool(Document):
	def validate(self):
		pass
	def on_submit(self):
		pass
	def on_cancel(self):
		pass

	pass


@frappe.whitelist()
def build_social_security_salaries(posting_date, employee_share_rate=0, department="", branch=""):
	employees=[]
	if branch != "" and department != "":
		employees= frappe.db.sql(f"""
			select employee
			from `tabEmployee`
			where branch ='{branch}' and department ='{department}'""",as_dict=True)
	elif branch !="":
		employees= frappe.db.sql(f"""
			select employee
			from `tabEmployee`
			where branch ='{branch}'""",as_dict=True)
	else:
		employees= frappe.db.sql(f"""
			select employee
			from `tabEmployee`
			where department ='{department}'""",as_dict=True)
	for employee in employees:
		employee_doc=frappe.get_doc("Employee", employee)
		employee_doc.employee_share_rate=employee_share_rate
		entry = {
			"employee": employee.employee,
			"posting_date": posting_date,

		}
		(frappe.new_doc("Employee Social Security Salary")
			.update(entry)
			.insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
