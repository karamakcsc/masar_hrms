# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
import frappe
# from __future__ import unicode_literals
import erpnext, json
from frappe import _, scrub, ValidationError
from frappe.utils import flt, comma_or, nowdate, getdate
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe.model.document import Document
from frappe.model.document import Document
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from frappe.model.document import Document

class EmployeeOvertime(Document):
	def __init__(self, *args, **kwargs):
		super(EmployeeOvertime, self).__init__(*args, **kwargs)

	def on_submit(self):
		defAddAdditionalSalary(self, self.employee, self.salary_component, self.total_amount, self.posting_date)

@frappe.whitelist()
def defAddAdditionalSalary(self,employee, salary_component, amount, payroll_date):
    entry = {
        "employee": self.employee,
        "salary_component": salary_component,
        "company": self.company,
        "currency": frappe.get_doc("Company", self.company).default_currency,
        "amount": flt(self.total_amount),
        "payroll_date": payroll_date,
    }
    (frappe.new_doc("Additional Salary")
        .update(entry)
        .insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
    frappe.db.commit()
