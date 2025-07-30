# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta , datetime
import calendar
from frappe.utils import add_months, get_last_day, getdate
from frappe.model.document import Document
from masar_hrms.masar_hrms.doctype.employee_loans.employee_loans import EmployeeLoans
set_loan_months = EmployeeLoans.set_loan_months
contract_end_date_validate = EmployeeLoans.contract_end_date_validate
dbr_validate = EmployeeLoans.dbr_validate
max_loan_months_validate = EmployeeLoans.max_loan_months_validate


class EmployeeLoansManagement(Document):
	def validate(self):
		if self.management_type == "Reschedule":
			self.get_loans()
			self.validate_new_date()
		if self.management_type == "Restructure":
			set_loan_months(self)
			max_loan_months_validate(self)
			self.overlapping_loans()
	def on_submit(self):
		if self.management_type == "Reschedule":
			self.reschedule_loans()
		if self.management_type == "Restructure":
			self.cancel_overlapping_loans()
			self.create_additional_salary()
	def on_cancel(self):
		# self.validate_cancel()
		if self.management_type == "Reschedule":
			self.revert_reschedule_loans()
		if self.management_type == "Restructure":
			self.revert_cancel_overlapping_loans()

	def get_loans(self):
		if not self.employee:
			frappe.throw("Please select an Employee.")
		
		loans_sql = frappe.db.sql("""
			SELECT 
				tas.payroll_date, 
				tas.amount, 
				tas.name,
				tels.accumulated_repayment_amount,
				tel.loan_amount,
				tels.name AS schedule_name,
				tel.name AS emp_loans_ref
			FROM `tabEmployee Loans` tel 
			INNER JOIN `tabEmployee Loans Schedule` tels ON tels.parent = tel.name 
			INNER JOIN `tabAdditional Salary` tas ON tels.additional_salary_ref = tas.name 
			WHERE tel.docstatus = 1 
   			AND tas.docstatus = 1 
			AND tas.payroll_date >= CURDATE()
			AND tel.employee = %s
			ORDER BY tas.payroll_date
		""", (self.employee,), as_dict=True)
		if not loans_sql:
			frappe.throw("No loans found for the selected employee.")
		if not self.loans_schedule:
			for loan in loans_sql:
				self.loan_amount = loan.loan_amount
				self.append("loans_schedule", {
					"schedule_date": loan.payroll_date,
					"repayment_amount": loan.amount,
					"accumulated_repayment_amount": loan.accumulated_repayment_amount,
					"emp_loans_ref": loan.emp_loans_ref, # Employee Loans reference
					"additional_salary_ref": loan.name, # Additional Salary reference
					"el_ref": loan.schedule_name, # Employee Loans Schedule (Child Table) reference
				})

	def validate_new_date(self):
		new_dates = []
		if self.loans_schedule:
			for loan in self.loans_schedule:
				new_dates.append(loan.schedule_date)
			for loan in self.loans_schedule:
				if loan.new_date:
					if loan.new_date in new_dates:
						frappe.throw(f"Duplicate new schedule date found: {loan.new_date}. Please ensure each new date is unique.")
					if loan.new_date < loan.schedule_date:
						frappe.throw(f"New date {loan.new_date} cannot be earlier than the original schedule date {loan.schedule_date}.")
					if loan.new_date == loan.schedule_date:
						frappe.throw(f"New date {loan.new_date} cannot be the same as the original schedule date {loan.schedule_date}.")
					if self.contract_end_date:
						if loan.new_date > self.contract_end_date:
							frappe.throw(f"New date {loan.new_date} cannot be later than the contract end date {self.contract_end_date}.")
					new_sch_date = datetime.strptime(loan.new_date, '%Y-%m-%d').date()
					last_day = calendar.monthrange(new_sch_date.year, new_sch_date.month)[1]
					if new_sch_date.day != last_day:
						frappe.throw(f"New date {loan.new_date} must be the last day of the month.")

	def reschedule_loans(self):
		if not self.loans_schedule:
			frappe.throw("No loans schedule found to reschedule.")
		
		for loan in self.loans_schedule:
			if loan.additional_salary_ref and loan.new_date:
				frappe.db.set_value("Additional Salary", loan.additional_salary_ref, "payroll_date", loan.new_date)
				frappe.db.set_value("Employee Loans Schedule", loan.el_ref, "schedule_date", loan.new_date)
				frappe.msgprint(f"Loan in {loan.emp_loans_ref} and {loan.additional_salary_ref}  rescheduled successfully.", alert=True, indicator='green')

	def revert_reschedule_loans(self):
		if not self.loans_schedule:
			frappe.throw("No loans schedule found to revert.")
		
		for loan in self.loans_schedule:
			if loan.additional_salary_ref and loan.schedule_date and loan.new_date:
				frappe.db.set_value("Additional Salary", loan.additional_salary_ref, "payroll_date", loan.schedule_date)
				frappe.db.set_value("Employee Loans Schedule", loan.el_ref, "schedule_date", loan.schedule_date)
				frappe.msgprint(f"Loan in {loan.emp_loans_ref} and {loan.additional_salary_ref} rescheduled reverted successfully.", alert=True, indicator='green')

	def set_repayment_amount(self):
		if not self.loan_amount:
			frappe.throw("Please set both Loan Amount and Total Months.")
		
		loan_amount_to_use = self.final_loan_amount or self.loan_amount
		
		if self.repayment_method == "Equal Monthly Installments":
			monthly_amount = loan_amount_to_use / self.total_months
			self.repayment_amount_month = round(monthly_amount, 3)
		elif self.repayment_method == "Custom Monthly Amount":
			if not self.repayment_amount_month:
				frappe.throw("Please set the Repayment Amount per Month.")
			if self.repayment_amount_month > self.loan_amount:
				frappe.throw("Repayment Amount per Month cannot be greater than Loan Amount.")
			monthly_amount = self.repayment_amount_month
			if self.start_date and monthly_amount:
				months = round(loan_amount_to_use / monthly_amount)
				self.total_months = months
				if not self.start_this_month:
					months += 1
				self.end_date = get_last_day(add_months(getdate(self.start_date), months - 1))
	
	def total_loan_validate(self):
		over_allowance_percent = frappe.db.get_value("Company", self.company, "custom_over_salary_allowance")
		if not over_allowance_percent:
			frappe.throw("Please set the Over Salary Restriction in Company settings.")
		if self.employee:
			emp_doc = frappe.get_doc("Employee", self.employee)
			earining_salary = 0
			for comp in emp_doc.custom_salary_component_table:
				if comp.is_active:
					if comp.type:
						if comp.type == "Earning" and comp_doc.is_social_security_applicable:
							earining_salary += comp.esc_amount
					else:
						comp_doc = frappe.get_doc("Salary Component", comp.salary_component)
						if comp_doc.type == "Earning" and comp_doc.is_social_security_applicable:
							earining_salary += comp.esc_amount
			total_salary = earining_salary
			osa_salary = (total_salary * over_allowance_percent) / 100
			if self.final_loan_amount > osa_salary:
				frappe.throw(f"Loan amount {self.final_loan_amount} exceeds over salary allowance {osa_salary}. Please adjust the loan amount or check the OSA settings in Company.")

 
	def overlapping_loans(self):
		if not self.loan_amount or not self.start_date:
			frappe.throw("Please set both Loan Amount and Start Date.")
		
		if self.repayment_method == "Equal Monthly Installments":
			if not self.total_months:
				frappe.throw("Please set Total Months.")
			self.end_date = get_last_day(add_months(getdate(self.start_date), self.total_months - 1))
		elif self.repayment_method == "Custom Monthly Amount":
			if not self.repayment_amount_month:
				frappe.throw("Please set the Repayment Amount per Month.")
			if self.repayment_amount_month > self.loan_amount:
				frappe.throw("Repayment Amount per Month cannot be greater than Loan Amount.")
			months = round(self.loan_amount / self.repayment_amount_month)
			if not self.start_this_month:
				months += 1
			self.end_date = get_last_day(add_months(getdate(self.start_date), months - 1))
		
		existing_loans = frappe.db.sql("""
			SELECT 
				tas.name AS additional_sal_ref, tas.amount, tas.payroll_date,
				tel.name AS emp_loans_ref, tels.name AS schedule_name
			FROM `tabEmployee Loans` AS tel
			INNER JOIN `tabEmployee Loans Schedule` AS tels ON tels.parent = tel.name
			INNER JOIN `tabAdditional Salary` tas ON tels.additional_salary_ref = tas.name 
			WHERE
				tel.employee = %s
				AND tel.docstatus = 1
				AND tas.docstatus = 1
				AND tas.payroll_date BETWEEN %s AND %s
		""", (self.employee, get_last_day(self.start_date), get_last_day(self.end_date)), as_dict=True)
		
		if not existing_loans:
			frappe.throw("No overlapping loans found for the selected employee within the specified date range.")

		self.set("loans_structure", [])
		self.overlapping_loan_amount = sum(loan.amount for loan in existing_loans)
		self.final_loan_amount = self.loan_amount + self.overlapping_loan_amount
		
		self.set_repayment_amount()
		contract_end_date_validate(self)
		dbr_validate(self)
		self.total_loan_validate()
		base_monthly = round(self.repayment_amount_month, 3)
		accumulated = 0
		start_date = getdate(self.start_date)

		if self.start_this_month:
			schedule_base = start_date.replace(day=1)
		else:
			schedule_base = add_months(start_date.replace(day=1), 1)
			
		for i in range(self.total_months):
			payment_date = get_last_day(add_months(schedule_base, i))

			if i == self.total_months - 1:
				repayment = round(self.final_loan_amount - accumulated, 3)
			else:
				repayment = base_monthly

			accumulated += repayment
			self.append("loans_structure", {
				"schedule_date": payment_date,
				"repayment_amount": repayment,
				"accumulated_repayment_amount": accumulated,
			})

		existing_loans = frappe.db.sql("""
			SELECT 
				tas.name AS additional_sal_ref, tas.amount, tas.payroll_date,
				tel.name AS emp_loans_ref, tels.name AS schedule_name
			FROM `tabEmployee Loans` AS tel
			INNER JOIN `tabEmployee Loans Schedule` AS tels ON tels.parent = tel.name
			INNER JOIN `tabAdditional Salary` tas ON tels.additional_salary_ref = tas.name 
			WHERE
				tel.employee = %s
				AND tel.docstatus = 1
				AND tas.docstatus = 1
				AND tas.payroll_date BETWEEN %s AND %s
		""", (self.employee, get_last_day(self.start_date), get_last_day(self.end_date)), as_dict=True)

		for loan in self.loans_structure:
			for existing_loan in existing_loans:
				if existing_loan.payroll_date == loan.schedule_date:
					loan.old_add_sal_ref = existing_loan.additional_sal_ref
					loan.emp_loans_ref = existing_loan.emp_loans_ref
					loan.el_ref = existing_loan.schedule_name

	def cancel_overlapping_loans(self):
		if self.loans_structure:
			for loan in self.loans_structure:
				if loan.old_add_sal_ref:
					ad_doc = frappe.get_doc("Additional Salary", loan.old_add_sal_ref).cancel()
					frappe.db.set_value("Employee Loans Schedule", loan.el_ref, "management_comments", f"Overlapping Loan {ad_doc.name} cancelled as part of Restructure Management # {self.name}.")

	def revert_cancel_overlapping_loans(self):
		if self.loans_structure:
			for loan in self.loans_structure:
				if loan.old_add_sal_ref:
					old_doc = frappe.get_doc("Additional Salary", loan.old_add_sal_ref)
					if old_doc.docstatus == 2:
						new_doc = frappe.copy_doc(old_doc)
						new_doc.docstatus = 0
						new_doc.insert(ignore_permissions=True)
						new_doc.submit()
						frappe.db.set_value("Employee Loans Schedule", loan.el_ref, "additional_salary_ref", new_doc.name)
						frappe.msgprint(f"Overlapping Loan {old_doc.name} reverted as {new_doc.name} successfully.", alert=True, indicator='green')

	def create_additional_salary(self):
		if self.loans_structure:
			for loan in self.loans_structure:
				additional_salary = frappe.new_doc("Additional Salary")
				additional_salary.employee = self.employee
				additional_salary.employee_name = self.employee_name
				additional_salary.department = self.department
				additional_salary.company = self.company
				additional_salary.is_recurring = 0
				additional_salary.payroll_date = loan.schedule_date
				additional_salary.salary_component = "Loan"
				additional_salary.type = "Deduction"
				additional_salary.amount = loan.repayment_amount
				additional_salary.deduct_full_tax_on_selected_payroll_date = 1
				additional_salary.overwrite_salary_structure_amount = 1
				additional_salary.ref_doctype = self.doctype
				additional_salary.ref_docname = self.name
				additional_salary.insert(ignore_permissions=True)
				additional_salary.submit()
				loan.additional_salary_ref = additional_salary.name
			self.save(ignore_permissions=True)
			frappe.msgprint(f"Additional Salary created for Employee {self.employee}", alert=True, indicator='green')

	# def validate_cancel(self):
	# 	other_type = "Restructure" if self.management_type == "Reschedule" else "Reschedule"
	# 	child_table = "loans_schedule" if self.management_type == "Reschedule" else "loans_structure"

	# 	loan_refs = {row.emp_loans_ref for row in self.get(child_table) if row.emp_loans_ref}
	# 	if not loan_refs:
	# 		return

	# 	loan_refs_str = "', '".join(loan_refs)

	# 	conflict = frappe.db.sql(f"""
	# 		SELECT elm.name, elm.management_type, elm.creation
	# 		FROM `tabEmployee Loans Management` elm
	# 		INNER JOIN `tab{ "Employee Loans Management Schedule" if self.management_type == "Reschedule" else "Employee Loans Management Structure" }` els
	# 			ON els.parent = elm.name
	# 		WHERE elm.employee = %s
	# 		AND elm.docstatus = 1
	# 		AND elm.management_type = %s
	# 		AND els.emp_loans_ref IN ('{loan_refs_str}')
	# 		AND elm.name != %s
	# 	""", (self.employee, other_type, self.name), as_dict=True)

	# 	if conflict:
	# 		conflict_docs = ", ".join(f"{row.name}" for row in conflict)
	# 		frappe.throw(f"""You cannot cancel this {self.management_type} management because a submitted {other_type} management exists 
	# 			for the same loan(s). Cancel the following first: {conflict_docs}.""")

	@frappe.whitelist()
	def get_basic_salary(self):
		emp_doc = frappe.get_doc("Employee", self.employee)
		co_doc = frappe.get_doc("Company", self.company)
		basic_salary_component = co_doc.custom_basic_salary_component
		for component in emp_doc.custom_salary_component_table:
			if component.salary_component == basic_salary_component and component.is_active:
				self.basic_salary = component.esc_amount
				return component.esc_amount
		return False