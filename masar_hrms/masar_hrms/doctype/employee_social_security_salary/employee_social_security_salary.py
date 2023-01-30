# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import frappe
# from frappe.model.document import Document
#
# class EmployeeSocialSecuritySalary(Document):
# 	pass

import erpnext, json
from frappe import _, scrub, ValidationError
from frappe.utils import flt, comma_or, nowdate, getdate
import datetime

from frappe.model.document import Document

class EmployeeSocialSecuritySalary(Document):
	def validate(self):
		pass

	def on_submit(self):
		fill_social_security_salary(self.employee, 1, self.amount, self.ss_emp_share_amount, self.ss_company_share_amount)

	def on_cancel(self):
		fill_social_security_salary(self.employee, 0)


	@frappe.whitelist()
	def calculate_social_security_amount(self):
		posting_date = datetime.datetime.strptime(self.posting_date, '%Y-%m-%d')
		if len(get_ss_doc(self.employee, posting_date.year)):
			frappe.throw(self.employee+" already have submitted document")
		ss_salary_slip=get_ss_salary_slip(self.employee, posting_date.year)
		total_ss_amount=0
		if not len(ss_salary_slip):
			#frappe.throw(self.employee + " don't have submitted salary slip for this date")
			entry = {
				"employee": self.employee,
				"posting_date": posting_date
			}
			salary_slip = frappe.new_doc('Salary Slip')
			salary_slip.update(entry)
			salary_slip.get_emp_and_working_day_details()
			for item in salary_slip.earnings:
				if frappe.get_doc("Salary Component", item.salary_component).is_social_security_applicable:
					total_ss_amount+=item.amount
			for item in salary_slip.deductions:
				if frappe.get_doc("Salary Component", item.salary_component).is_social_security_applicable:
					total_ss_amount-=item.amount
			total_ss_amount=max(0,total_ss_amount)
			total_ss_amount=min(5000,total_ss_amount)
		else:				
			salary_slip_name=ss_salary_slip[0].name
			salary_slip=frappe.get_doc("Salary Slip", salary_slip_name)
			for item in salary_slip.earnings:
				if frappe.get_doc("Salary Component", item.salary_component).is_social_security_applicable:
					total_ss_amount+=item.amount
			for item in salary_slip.deductions:
				if frappe.get_doc("Salary Component", item.salary_component).is_social_security_applicable:
					total_ss_amount-=item.amount
			total_ss_amount=max(0,total_ss_amount)
			total_ss_amount=min(5000,total_ss_amount)
			# self.amount=total_ss_amount
			# self.ss_company_share_amount=total_ss_amount*flt(self.company_share_rate)
			# self.ss_emp_share_amount=total_ss_amount*flt(self.employee_share_rate)
		return total_ss_amount

@frappe.whitelist()
def get_ss_salary_slip(employee, year):
	return frappe.db.sql(f"""
		select name
		from `tabSalary Slip` tss
		where tss.docstatus=1 and employee='{employee}' and year(posting_date)='{year}'
		order by month(posting_date) asc""",as_dict=True)

@frappe.whitelist()
def get_ss_doc(employee, year):
	return frappe.db.sql(f"""
		select name
		from `tabEmployee Social Security Salary` tsss
		where tsss.docstatus=1 and employee='{employee}' and year(posting_date)='{year}'""",as_dict=True)

@frappe.whitelist()
def fill_social_security_salary(employee, status, amount=0, emp_share=0, company_share=0):
	employee_doc=frappe.get_doc("Employee", employee)
	if status==1:
		employee_doc.social_security_salary=amount
		employee_doc.social_security_amount=emp_share
		employee_doc.save()
	elif status==0:
		employee_doc.social_security_salary=0
		employee_doc.social_security_amount=0
		employee_doc.save()
