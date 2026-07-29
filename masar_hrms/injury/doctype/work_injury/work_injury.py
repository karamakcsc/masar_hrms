# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import qb, _ , bold
from frappe.utils import flt
from frappe.utils import add_days, getdate
from frappe.model.document import Document

from masar_hrms.injury.doctype.work_injury_settings.work_injury_settings import get_settings


class WorkInjury(Document):
	def validate(self):
		self.validate_days()
		self.set_totals()
		self.validate_medical_approval()
		self.validate_treatment_cost_limit()

	def on_submit(self):
		self.create_leave()
	def on_update_after_submit(self):
		self.create_leave()

	def validate_medical_approval(self):
		settings = get_settings()
		if settings.require_medical_approval and not self.is_medically_approved:
			frappe.throw(
				_("This Work Injury cannot be submitted until Medical Approval is completed."),
				title=_("Medical Approval Required"),
			)

	def validate_treatment_cost_limit(self):
		settings = get_settings()
		if not settings.cost_limit:
			return
		if flt(self.total_cost_of_treatment) <= flt(settings.treatment_cost_limit):
			return

		message = _("Total Cost of Treatment ({0}) exceeds the configured limit of {1}.").format(
			bold(self.total_cost_of_treatment), bold(settings.treatment_cost_limit)
		)
		if settings.action_for_cost_limit == "Stop":
			frappe.throw(message, title=_("Treatment Cost Limit Exceeded"))
		elif settings.action_for_cost_limit == "Warn":
			frappe.msgprint(message, title=_("Treatment Cost Limit Exceeded"), indicator="orange")

	def validate_days(self):
		if self.injuries:
			for injury in self.injuries:
				if injury.no_of_days and injury.no_of_days < 0:
					frappe.throw(
						f"Number of Days cannot be negative in row {injury.idx}",
						title="Invalid Number of Days",
						)
	
	@frappe.whitelist()
	def set_num_of_days_total(self):
		self.total_days = flt(sum(flt(injury.no_of_days) for injury in self.injuries))

	@frappe.whitelist()
	def set_cost_total(self):
			self.total_cost_of_treatment = flt(sum(flt(injury.cost_of_treatment) for injury in self.injuries))

	@frappe.whitelist()
	def set_totals(self):
		self.total_days = flt(sum(flt(injury.no_of_days) for injury in self.injuries))
		self.total_cost_of_treatment = flt(sum(flt(injury.cost_of_treatment) for injury in self.injuries))

		employee_paid_days = flt(get_settings().employee_paid_days)
		self.employer_paid_days = min(self.total_days, employee_paid_days)
		self.deduction_days = max(0, self.total_days - employee_paid_days)

	@frappe.whitelist()
	def set_end_date(self):
		if not self.injury_start_date:
			frappe.throw(_("Please set Injury Start Date"))

		start_date = getdate(self.injury_start_date)
		if not self.injuries:
			return
		for idx, row in enumerate(self.injuries):
			if row.no_of_days:
				row.start_date = start_date
				'if start date 01-01-2025 and no of days 1 the end date 01-01-2025'
				row.end_date = add_days(start_date, row.no_of_days - 1)
				'save the start date as end date + 1'
				start_date = add_days(row.end_date, 1)
	def create_leave(self):
		if not self.injuries:
			frappe.throw(_("No injuries found to create leave application."))
		start_date = self.injury_start_date
		for row in self.injuries:
			if row.is_calc == 1:
				start_date = add_days(row.end_date, 1)
				continue
			new_leave = frappe.new_doc("Leave Application")
			new_leave.employee = self.employee
			new_leave.leave_type = get_leave_type()
			new_leave.from_date = start_date
			new_leave.to_date = row.end_date
			new_leave.total_leave_days = row.no_of_days
			new_leave.description = f"Injury Leave for {self.employee_name} from {start_date} to {row.end_date} for {row.no_of_days} days.",
			new_leave.status = "Approved"
			new_leave.posting_date = self.posting_date
			new_leave.leave_approver = get_leave_approver(self.employee)
			new_leave.custom_work_injury_ref = self.name
			new_leave.insert()
			new_leave.submit()
			
			frappe.msgprint(_(f"""Leave Application {bold(new_leave.name)} created for Injury Leave from {start_date} 
									to {row.end_date} for {row.no_of_days} days."""
							))
			row.is_calc = 1
			row.db_update()
			start_date = add_days(row.end_date, 1)
  
def get_leave_approver(employee):
		leave_approver, department = frappe.db.get_value("Employee", employee, ["leave_approver", "department"])

		if not leave_approver and department:
			leave_approver = frappe.db.get_value(
				"Department Approver",
				{"parent": department, "parentfield": "leave_approvers", "idx": 1},
				"approver",
		)

		return leave_approver
					
def get_leave_type():
	settings = frappe.get_doc("Work Injury Settings")
	leave_type = settings.leave_type
	if not leave_type:
		frappe.throw(_("No Injury Leave Type found. Please set a Leave Type as Injury."))
	return leave_type
