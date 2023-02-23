# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
#
import json

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.desk.reportview import get_filters_cond, get_match_cond
from frappe.model.document import Document
from frappe.query_builder.functions import Coalesce
from frappe.utils import (
	DATE_FORMAT,
	add_days,
	add_to_date,
	cint,
	comma_and,
	date_diff,
	flt,
	get_link_to_form,
	getdate,
)

import erpnext
# from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
# 	get_accounting_dimensions,
# )
# from erpnext.accounts.utils import get_fiscal_year
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
class EmployeeSocialSecuritySalaryEntry(Document):
	@frappe.whitelist()
	def fill_employee_details(self):
		self.set("employees", [])
		employees = self.get_emp_list()
		if not employees:
			error_msg = _(
				"No employees found for the mentioned criteria:<br>Company: {0}<br> Currency: {1}<br>Payroll Payable Account: {2}"
			).format(
				frappe.bold(self.company),
				frappe.bold(self.currency),
				frappe.bold(self.payroll_payable_account),
			)
			if self.branch:
				error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
			if self.department:
				error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
			if self.designation:
				error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
			# if self.start_date:
			# 	error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
			# if self.end_date:
			# 	error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
			frappe.throw(error_msg, title=_("No employees found"))

		for d in employees:
			self.append("employees", d)

		self.number_of_employees = len(self.employees)
		if self.validate_attendance:
			return self.validate_employee_attendance()

	def check_mandatory(self):
		for fieldname in ["company", "start_date", "end_date"]:
			if not self.get(fieldname):
				frappe.throw(_("Please set {0}").format(self.meta.get_label(fieldname)))
