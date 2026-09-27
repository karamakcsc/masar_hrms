# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import NullIf, Sum
from frappe.model.document import Document

#### Last Update By Mahmoud 26-1-2025
class EmployeeSocialSecuritySalary(Document):

	@frappe.whitelist()
	def get_share_persent(self):
		"""
		Get Employee Share Rate from Employee Doctype if Null Get the Default from Company
		Get the Company Share Rate from Company depends on Employee Is Hazard to check if Dangerous or not
		"""
		if not self.employee or not self.company:
			return False

		emp_share_rate, company_share_rate = 0, 0
		company_doc = frappe.get_doc("Company", self.company)
		emp_doc = frappe.get_doc("Employee", self.employee)

		# Employee share
		if emp_doc.employee_share_rate not in [None, 0]:
			emp_share_rate = emp_doc.employee_share_rate
		else:
			emp_share_rate = company_doc.employee_share_rate

		# Company share depends on hazard
		if (emp_doc.custom_is_hazard or 0) == 0:
			company_share_rate = company_doc.company_share_rate
		else:
			company_share_rate = company_doc.custom_company_share_rate_dangerous

		self.employee_share_rate = emp_share_rate or 0
		self.company_share_rate = company_share_rate or 0
		return True

	@frappe.whitelist()
	def get_social_security_salary(self):
		"""
		Get the Default Social Security Salary From the Active and SS applicable Components
		"""
		if not self.employee:
			self.social_security_salary = 0
			return False

		sc = frappe.qb.DocType("Salary Component")
		est = frappe.qb.DocType("Employee Salary Table")

		amount_sql = (
			frappe.qb.from_(est)
			.select((NullIf(Sum(est.esc_amount), 0)).as_("amount"))
			.left_join(sc).on(est.salary_component == sc.name)
			.where(est.is_active == 1)
			.where(sc.is_social_security_applicable == 1)
			.where(est.parent == self.employee)
		).run()

		amount = 0
		if amount_sql and amount_sql[0] and amount_sql[0][0] is not None:
			amount = amount_sql[0][0]
		self.social_security_salary = amount or 0
		return True

	@frappe.whitelist()
	def calculate_share_amount(self):
		"""
		Depends on Social Salary and Rates get the amount for Employee and Company
		"""
		salary = float(self.social_security_salary or 0)
		emp_rate = float(self.employee_share_rate or 0)
		comp_rate = float(self.company_share_rate or 0)

		self.ss_emp_share_amount = (emp_rate * salary) / 100 if emp_rate else 0
		self.ss_company_share_amount = (comp_rate * salary) / 100 if comp_rate else 0

	def _should_recalculate(self):
		"""
		Recalculate if:
		- New document
		- Employee / Company changed
		- social_security_salary_entry changed (your flag/field)
		"""
		if self.is_new():
			return True

		prev = self.get_doc_before_save()
		if not prev:
			return True

		important_fields = ["employee", "company", "social_security_salary_entry"]
		for f in important_fields:
			if (prev.get(f) or None) != (self.get(f) or None):
				return True

		return False

	def validate(self):
		# On NEW: always fetch + calculate everything
		# On existing: only refetch if key fields changed
		if self._should_recalculate():
			
			self.get_share_persent()
			self.get_social_security_salary()
		# Always re-calc amounts (rates/salary might be manually edited too)
		self.calculate_share_amount()

	def on_submit(self):
		cont = self.ss_amount_validation()
		if not cont:
			# better to stop submit clearly (instead of forcing docstatus back)
			frappe.throw(
				"Submission stopped بسبب خطأ في قيمة Employee Share. راجع الرسالة السابقة.",
				title=frappe._("Employee Share Validation"),
			)

		self.filled_in_employee()

	def on_cancel(self):
		self.reset_in_employee()

	def ss_amount_validation(self):
		msg = f"""Employee <b>{self.employee}</b> : The Employee Share amount must be greater than zero.
Please verify the Employee Share Rate for the Social Security Salary."""
		if self.ss_emp_share_amount in [None, 0] and self.social_security_salary_entry is None:
			frappe.throw(msg, title=frappe._("Employee Share Validation"))

		elif self.ss_emp_share_amount in [None, 0] and self.social_security_salary_entry is not None:
			frappe.msgprint(
				msg,
				title=frappe._("Employee Share Validation"),
				indicator="red",
			)
			return False

		return True

	def filled_in_employee(self):
		"""Set the Effect to Employee File"""
		emp_doc = frappe.get_doc("Employee", self.employee)
		emp_doc.social_security_salary = self.social_security_salary or 0
		emp_doc.social_security_amount = self.ss_emp_share_amount or 0
		emp_doc.save()
		frappe.msgprint(
			"Employee Social Security Details Updated Successfully",
			alert=True,
			indicator="green",
		)

	def reset_in_employee(self):
		"""Reset the Employee Social Security Details to Zero"""
		emp_doc = frappe.get_doc("Employee", self.employee)
		emp_doc.social_security_salary = 0
		emp_doc.social_security_amount = 0
		emp_doc.save()
		frappe.msgprint(
			"Employee Social Security Details Updated Successfully",
			alert=True,
			indicator="blue",
		)
