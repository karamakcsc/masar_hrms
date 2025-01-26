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
		then , 
		Get the Company Share Rate from Company depends on Employee Is Hazard to check if Dangerous or not 
		"""
		if self.employee:
			emp_share_rate  , company_share_rate = 0 , 0 
			company_doc = frappe.get_doc('Company' , self.company)
			emp_doc = frappe.get_doc('Employee' , self.employee)
			if emp_doc.employee_share_rate not in [None , 0]:
				emp_share_rate = emp_doc.employee_share_rate
			else: 
				emp_share_rate = company_doc.employee_share_rate
			if emp_doc.custom_is_hazard == 0:
				company_share_rate = company_doc.company_share_rate
			else:
				company_share_rate = company_doc.custom_company_share_rate_dangerous
			self.employee_share_rate = emp_share_rate
			self.company_share_rate = company_share_rate
			return True

		return False
	@frappe.whitelist()
	def get_social_security_salary(self):
		"""
			Get the Default Social Security Salary From the Active and SS applicable Components
  		"""
		sc = frappe.qb.DocType('Salary Component')
		est = frappe.qb.DocType('Employee Salary Table')
		amount_sql  = (
			frappe.qb.from_(est)
			.select((NullIf(Sum( est.esc_amount) , 0 )).as_('amount'))
			.left_join(sc).on(est.salary_component ==sc.name )
			.where(est.is_active == 1).where( sc.is_social_security_applicable == 1 )
			.where(est.parent == self.employee)
		).run()
		amount = 0 
		if amount_sql:
			amount = amount_sql[0][0]
		self.social_security_salary = amount
		return True
	@frappe.whitelist()
	def calculate_share_amount(self):
		"""
			Depends on Social Salary and Rates get the amount for Employee and Company
  		"""
		if self.employee_share_rate: 
			self.ss_emp_share_amount = (
				(float(self.employee_share_rate) if self.employee_share_rate else 0 )
												*
				(float(self.social_security_salary) if self.social_security_salary else 0 )
			)/100
		else : 
			self.ss_emp_share_amount = 0 
   
		if self.employee_share_rate: 
			self.ss_company_share_amount = (
				(float(self.company_share_rate) if self.company_share_rate else 0 )
												*
				(float(self.social_security_salary) if self.social_security_salary else 0 )
			)/100
		else : 
			self.ss_company_share_amount = 0 
	def validate(self): 
		self.calculate_share_amount()
	def on_submit(self):
		self.ss_amount_validation()
		self.filled_in_employee()
	def on_cancel(self): 
		self.reset_in_employee()
  
  
	def ss_amount_validation(self): 
		if self.ss_emp_share_amount in [None , 0 ]: 
			frappe.throw('''
                The Employee Share amount must be greater than zero. Please verify the Employee Share Rate for the Social Security Salary.'''
             , title= frappe._('Employee Share Validation')
            )
	def filled_in_employee(self):
		"""
			Set the Effect to Employee File 
  		"""
		emp_doc = frappe.get_doc('Employee' , self.employee)
		emp_doc.social_security_salary = self.social_security_salary
		emp_doc.social_security_amount = self.ss_emp_share_amount
		emp_doc.save()
		frappe.msgprint(
      			'Employee Social Security Details Updated Successfully' , 
         		alert = True , 
           		indicator='green')
	def reset_in_employee(self):
		"""
			Reset the Employee Social Security Details to Zero 
  		"""
		emp_doc = frappe.get_doc('Employee' , self.employee)
		emp_doc.social_security_salary = 0
		emp_doc.social_security_amount = 0
		emp_doc.save()
		frappe.msgprint(
      			'Employee Social Security Details Updated Successfully' , 
         		alert = True , 
           		indicator='green')
  
  