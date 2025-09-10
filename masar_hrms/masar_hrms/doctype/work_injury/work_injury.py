# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import  Sum
from frappe import qb, _ , bold 
from frappe.utils import flt
from frappe.utils import add_days, getdate
from frappe.model.document import Document


class WorkInjury(Document):
	def validate(self):
		self.validate_days()
		self.set_totals()
		self.set_leave_rate()
	def on_submit(self):
		self.create_leave()
	def on_update_after_submit(self):
		self.create_leave()

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
		self.total_days = sum(injury.no_of_days for injury in self.injuries) if self.injuries else 0

	@frappe.whitelist()
	def set_cost_total(self):
			self.total_cost_of_treatment = sum(injury.cost_of_treatment for injury in self.injuries) if self.injuries else 0
	
	def set_totals(self):
		self.total_days = sum(injury.no_of_days for injury in self.injuries) if self.injuries else 0
		self.total_cost_of_treatment = sum(injury.cost_of_treatment for injury in self.injuries) if self.injuries else 0

	def number_of_day(self):
		return 30 
	def set_leave_rate(self): 
		if self.employee is None:
			self.rate_for_leaves = 0
		est = qb.DocType('Employee Salary Table')
		earning_salary = (
      		qb.from_(est)
        	.where(est.parent == self.employee)
         	.where(est.is_active == 1)
		 	.where(est.type == 'Earning')
			.select(Sum(est.esc_amount))
   		).run()
		self.rate_for_leaves = float(
			flt(earning_salary[0][0] if earning_salary else 0) / flt(self.number_of_day())
		) if earning_salary else 0

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
				row.end_date = add_days(start_date, row.no_of_days) # if start date 01-01-2025 and no of days 1 the end date 02-01-2025
				start_date = add_days(row.end_date, 1)  # save the start date as end date + 1

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
			new_leave.save()
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
	lt = frappe.qb.DocType("Leave Type")
	leave_type = (
		qb.from_(lt)
		.where(lt.custom_is_injury == 1)
		.select(lt.name)
	).run(as_dict=True)
	if leave_type:
		if len(leave_type) > 1:
			frappe.throw(_("More than one Injury Leave Type found. Please ensure only one is set as Injury."))
		return leave_type[0].name
