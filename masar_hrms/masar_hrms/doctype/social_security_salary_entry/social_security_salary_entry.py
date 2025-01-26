# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
### Last Update by Mahmoud 26-1-2025
class SocialSecuritySalaryEntry(Document):			
	@frappe.whitelist()
	def fill_employee_details(self):
		e = frappe.qb.DocType('Employee')
		sql = (
			frappe.qb.from_(e)
			.select(e.name , e.employee_name , e.department , e.branch , e .designation)
		)
		if self.branch:
			sql = sql.where(e.branch == self.branch)
		if self.department:
			sql = sql.where(e.department == self.department)
		if self.designation:
			sql = sql.where(e.designation == self.designation)
		if self.employee_status:
			sql = sql.where(e.status == self.employee_status)
		if self.work_type: 
			sql = sql.where(e.work_type == self.work_type)
		return sql.run(as_dict=True)
	def get_employee_len(self):
		self.number_of_employees = len(self.employees)
	def validate(self):
		self.get_employee_len()
	def get_existing( self, employee): 
		esss = frappe.qb.DocType('Employee Social Security Salary')
		exist = (
      		frappe.qb.from_(esss).select(esss.name)
        .where(esss.employee == employee)
        .where(esss.posting_date == self.posting_date)
        .where(esss.docstatus ==1 )).run(as_dict = True)
		if len(exist) !=0 : 
			return True
		return False 
  
	def on_submit(self):
		self.insert_esss()
     
	def insert_esss(self):
		existing_emp = list()
		for e in self.employees: 
			if self.get_existing(employee = e.employee): 
				existing_emp.append({
					"emp": f"{e.employee}", 
					"name" : f"{self.posting_date}-{e.employee_name}"
				})
			else: 
				entry = {
					'posting_date' : self.posting_date, 
					'company' : self.company, 
					'employee' : e.employee, 
					'social_security_salary_entry' : self.name
				}
				frappe.new_doc('Employee Social Security Salary').update(entry).insert(ignore_permissions=True)
		if len(existing_emp) != 0: 
			msg ='The Employee Social Security Salary is created For All Employee Except The Employees :<br>'
			for exist in existing_emp:
				msg += f"Employee: {exist['emp']} Exist in {exist['name']} <br>"
			frappe.msgprint(msg , title=frappe._('Existing Employee Social Security Salary'))
		else: 
			frappe.msgprint('Employee Social Security Salary Created Successfully', alert=True , indicator = 'green')
	@frappe.whitelist()
	def submit_esss(self): 
		esss = frappe.qb.DocType('Employee Social Security Salary')
		draft = (
      		frappe.qb.from_(esss)
        .select(esss.name , esss.docstatus)
        .where(esss.social_security_salary_entry == self.name)
        ).run(as_dict = True)
		for d in draft: 
			if d.docstatus == 0 : 
				doc = frappe.get_doc('Employee Social Security Salary' , d.name)
				doc.run_method('submit')
		frappe.db.set_value(self.doctype , self.name , 'status' , 'Submitted')
		frappe.msgprint('Employee Social Security Salary Submitted Successfully', alert=True , indicator = 'green')
		return True
