# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
#
# class ShortLeaveApplication(Document):
# 	pass

#

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

class InvalidShortLeaveApplication(ValidationError):
	pass

class ShortLeaveApplication(Document):
	def __init__(self, *args, **kwargs):
		super(ShortLeaveApplication, self).__init__(*args, **kwargs)

	def validate(self):
		pass
	

	def on_update(self):

		if self.status == "Open" and self.docstatus < 1:
			# notify leave approver about creation
			if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
				self.notify_leave_approver()

		share_doc_with_approver(self, self.leave_approver)

	def on_submit(self):
		from_time = get_time(self.from_time)
		posting_date = datetime.combine(self.posting_date, from_time)  # No need to call .date()

		result = get_employee_shift(self.employee, posting_date)  # Define and assign a value to `result`

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
			frappe.throw("You have to assign a shift for the employee or assign standard working hours in HR Settings")

		# if self.total_leave_hours/3600.0>self.leave_balance*working_hours*3600:
		# 	frappe.throw(
		# 		_("Leave hours is greater than remaining allowed hours")
		# 	)

		if self.status in ["Open", "Cancelled"]:
			frappe.throw(
				_("Only Short Leave Applications with status 'Approved' and 'Rejected' can be submitted")
			)
		
		if self.leave_type:	
			leave_type = frappe.get_doc("Leave Type", self.leave_type)

			if leave_type.is_lwp == 0:
				if self.leave_balance * working_hours < self.total_leave_hours:
					frappe.throw(_("Insufficient leave balance. Requested leaves exceed available balance."))

				# notify leave applier about approval
				if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
					self.notify_employee()

				self.create_leave_ledger_entry(str(working_hours))
			else:
				if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
					self.notify_employee()
					
				self.AddAdditionalSalary()	

	def on_cancel(self):
		# self.create_leave_ledger_entry(submit=False)
		# notify leave applier about cancellation
		if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
			self.notify_employee()
		pass

	def on_update(self):
		self.reload()
		pass

	def create_leave_ledger_entry(self,working_hours, submit=True):
		raise_exception = False if frappe.flags.in_patch else True
		args = dict(
			leaves=((self.total_leave_hours)/flt(working_hours)) * -1,
			from_date=self.posting_date,
			to_date=self.posting_date,
			is_lwp=0,
			holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
			or "",
		)
		create_leave_ledger_entry(self, args, submit)

	def AddAdditionalSalary(self, submit=True):
		employee = self.employee
		salary_component = self.salary_component
		payroll_date = self.posting_date.strftime("%Y-%m-%d")		
		working_hours = calculate_working_hours(employee,payroll_date)
		hour_rate = hour_rate = flt(self.basic_salary) / 240
		deduct_amount = self.total_leave_hours * hour_rate
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



	def notify_leave_approver(self):
		if self.leave_approver:
			parent_doc = frappe.get_doc("Short Leave Application", self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("HR Settings", "leave_approval_notification_template")
			if not template:
				frappe.msgprint(
					_("Please set default template for Leave Approval Notification in HR Settings.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response, args)

			self.notify(
				{
					# for post in messages
					"message": message,
					"message_to": self.leave_approver,
					# for email
					"subject": email_template.subject,
				}
			)

	def notify_employee(self):
		employee = frappe.get_doc("Employee", self.employee)
		if not employee.user_id:
			return

		parent_doc = frappe.get_doc("Short Leave Application", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "leave_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Leave Status Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)

		self.notify(
			{
				# for post in messages
				"message": message,
				"message_to": employee.user_id,
				# for email
				"subject": email_template.subject,
				"notify": "employee",
			}
		)


	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject
		if cint(self.follow_via_email):
			contact = args.message_to
			if not isinstance(contact, list):
				if not args.notify == "employee":
					contact = frappe.get_doc("User", contact).email or contact

			sender = dict()
			sender["email"] = frappe.get_doc("User", frappe.session.user).email
			sender["full_name"] = get_fullname(sender["email"])

			try:
				frappe.sendmail(
					recipients=contact,
					sender=sender["email"],
					subject=args.subject,
					message=args.message,
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass
@frappe.whitelist()
def calculate_to_time(from_time,total_leave_hours):
 
    # convert the from_time and total_leave_hours to datetime objects
	from_time_obj = datetime.strptime(from_time, '%H:%M:%S')
	total_leave_hours_obj = timedelta(hours=float(total_leave_hours)/3600)
	#frappe.msgprint(str(total_leave_hours_obj))
    # add the total_leave_hours to the from_time
	to_time_obj = from_time_obj + total_leave_hours_obj
	to_time = to_time_obj.strftime('%H:%M:%S')
	#frappe.msgprint(str(to_time))
	# set the to_time field
	return to_time

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