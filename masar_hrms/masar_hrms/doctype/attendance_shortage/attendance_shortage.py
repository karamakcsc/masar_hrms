# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
import frappe, erpnext, json,datetime
import time
from datetime import date, datetime, time, timedelta
from frappe import _, scrub, ValidationError
from frappe.utils import cint, get_datetime, get_time, getdate
from frappe.model.document import Document
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from frappe.utils import flt, comma_or, nowdate, getdate
from hrms.hr.utils import (
	get_holiday_dates_for_employee,
	share_doc_with_approver,
)

from typing import Dict

from frappe.utils import (
	cint,
	get_fullname,
)

from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange

from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

class AttendanceShortage(Document):
	pass


class AttendanceShortage(Document):
	def __init__(self, *args, **kwargs):
		super(AttendanceShortage, self).__init__(*args, **kwargs)

	def validate(self):
		pass
	

	def on_update(self):

		if self.status == "Open" and self.docstatus < 1:
			# notify leave approver about creation
			if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
				self.notify_leave_approver()

		share_doc_with_approver(self, self.leave_approver)

	def on_submit(self):
		
		# from_time = get_time(self.from_time)
		attendance_date = datetime.strptime("20-03-2023", "%d-%m-%Y").date()
		posting_date = datetime.combine(attendance_date, datetime.min.time())
		result=get_employee_shift(self.employee, posting_date)
		
		working_hours=0
		if result:
			if result.start_datetime.minute>result.end_datetime.minute:
				working_hours=datetime.time(result.end_datetime.hour-result.start_datetime.hour-1,60-result.start_datetime.minute+result.end_datetime.minute)
			else:
				working_hours=datetime.time(result.end_datetime.hour-result.start_datetime.hour,result.end_datetime.minute-result.start_datetime.minute)
		elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
			working_hours=frappe.db.get_single_value("HR Settings", "standard_working_hours")
		else: frappe.throw("You have to assign a shift for the employee or assign standar working hours in HR Settings")


		if self.salary_component is None:
			frappe.throw(
				_("Please Insert The Salary Componanet For This Employee")
			)

			if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
				self.notify_employee()

				self.create_leave_ledger_entry(str(working_hours))
			else:
				if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
					self.notify_employee()
					
		self.AddAdditionalSalary()

	def AddAdditionalSalary(self, submit=True):
		employee = self.employee
		salary_component = self.salary_component
		payroll_date = self.attendance_date			
		working_hours = calculate_working_hours(employee,payroll_date)
		
		hour_rate = flt(self.basic_salary) / 240
		deduct_amount = self.difference_hours * hour_rate
		entry = {
			"employee": employee,
			"salary_component": salary_component,
			"company": self.company,
			"currency": frappe.get_doc("Company", self.company).default_currency,
			"amount": flt(deduct_amount),
			"payroll_date": payroll_date,

		}
		(frappe.new_doc("Additional Salary")
			.update(entry)
			.insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
		frappe.db.commit()





@frappe.whitelist()
def calculate_working_hours(employee, posting_date):
    posting_date = datetime.strptime(posting_date, "%Y-%m-%d") 
    result = get_employee_shift(employee, posting_date)
    working_hours = 0

    if result:
        if result.start_datetime.minute > result.end_datetime.minute:
            working_hours = datetime.time(
                result.end_datetime.hour - result.start_datetime.hour - 1,
                60 - result.start_datetime.minute + result.end_datetime.minute
            )
        else:
            working_hours = datetime.time(
                result.end_datetime.hour - result.start_datetime.hour,
                result.end_datetime.minute - result.start_datetime.minute
            )
    elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
        working_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
    else:
        working_hours = 0

    return working_hours



@frappe.whitelist()
def get_salary_structure_assignment(employee=None):
    result = frappe.get_list(
        "Salary Structure Assignment",
        filters={'employee': employee, 'docstatus': 1},
        fields=['name'],
        order_by='creation DESC',
        limit=1
    )

    if result:
        return result[0].name
    else:
        return 0
    doc.save()