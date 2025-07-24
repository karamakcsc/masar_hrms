# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import db, qb , get_doc , throw , bold , _
from datetime import timedelta , datetime
from masar_hrms.masar_hrms.doctype.employee_attendance_process.employee_attendance_process import EmployeeAttendanceProcess as EAP
class EmployeeAttendanceProcessBulk(Document):

	@frappe.whitelist()
	def insert_employees(self): 
		e = qb.DocType('Employee')
		employees = (
      		qb.from_(e).select(e.name , e.employee_name , e.department , e.designation )
			.where(e.status == 'Active').where(e.is_overtime_applicable == 1 )
		)
		if self.department:
			employees = employees.where(e.department == self.department)
		if self.branch:
			employees = employees.where(e.branch == self.branch)
		if self.designation:
			employees = employees.where(e.designation == self.designation)
		if self.work_type:
			employees = employees.where(e.work_type == self.work_type)
		if self.grade:
			employees = employees.where(e.grade == self.grade)
		emp = employees.run(as_dict = True)
		self.set("employees", [])
		for e in emp: 
			self.append("employees", {
						"employee": e.name,
						"employee_name": e.employee_name,
						"department": e.department, 
						"designation": e.designation
					})
		return True
	@frappe.whitelist()
	def get_standard_date_period(self): 
		if self.posting_date is None: 
			return False
		posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d').date()
		start_month = posting_date.replace(day=1)
		next_month = start_month.replace(day=28) + timedelta(days=4) 
		end_month = next_month - timedelta(days=next_month.day)
		return {
			'from_date': start_month, 
			'to_date' : end_month
		}
	@frappe.whitelist()
	def get_salary_details(self , employee=None): 
		if employee is None: 
			employee = self.employee
		if employee is None: 	
			return {
				'basic_salary' : 0 , 
				'hour_rate' : 0 
		}
		est = qb.DocType('Employee Salary Table')
		basic_salary = (
      		qb.from_(est)
        	.where(est.parent == employee)
         	.where(est.is_active == 1)
			.where(est.salary_component == self.get_basic_salary_component())
			.select(est.esc_amount)
   		).run()
		standard_working_hours = get_doc('HR Settings').standard_working_hours
		if standard_working_hours in [0 , None]: 
			standard_working_hours = 8 ###### if not define defualt is 8 hours
		hour_rate = float(
			( basic_salary[0][0] if basic_salary else 0) / 
			(standard_working_hours * self.number_of_day() )
		)
		return {
			'basic_salary' : basic_salary[0][0] if basic_salary else 0  , 
			'hour_rate' : round(hour_rate , 3)
		}
	def validate(self):
		self.employee_validate()
		self.date_validate()
	def on_submit(self):
		self.create_employee_att_process()
	def employee_validate(self): 
		for e in self.employees:
			basic_salary = self.get_salary_details(employee=e.employee)['basic_salary']
			if basic_salary in [0 , None]: 
				throw(_(f"Employee {bold(e.employee)} must have an active Basic Salary component."))
			if not db.get_value('Employee' , e.employee , 'is_overtime_applicable'): 
				throw(_(f"Employee {bold(e.employee)} must be marked as overtime applicable."))
    
	def date_validate(self): 
		if not (self.from_date <= self.posting_date <= self.to_date): 
			throw(_(f"Posting Date must be within the period between {bold(self.from_date)} and {bold(self.to_date)}."))
		for e in self.employees:
			overlapping = frappe.db.exists(
				'Employee Attendance Process',
				{
					"employee": e.employee,
					"docstatus": ["!=", 2], 
					"from_date": ["<=", self.to_date],
					"to_date": [">=", self.from_date],
				}
			)
			if overlapping:
				throw(_(f"An overlapping record already exists for Employee {bold(e.employee)} within the period {bold(self.from_date)} to {bold(self.to_date)}."))
   
   
	def create_employee_att_process(self): 
		for e in self.employees: 
			eap = frappe.new_doc('Employee Attendance Process')
			eap.employee = e.employee 
			eap.employee_name = e.employee_name 
			eap.department = e.department
			eap.posting_date = self.posting_date
			eap.from_date = self.from_date 
			eap.to_date = self.to_date 
			eap.eapb_ref = self.name
			salary = EAP.get_salary_details(eap)
			eap.basic_salary = salary.get('basic_salary')
			eap.basic_salary_hour_rate = salary.get('hour_rate')
			EAP.get_overtime_type_as_defualt(eap)
			eap.save()
	def number_of_day(self):
		return 30 
	def get_basic_salary_component(self): 
		basic = db.get_value('Company' , self.company , 'custom_basic_salary_component')
		if basic is None:
			throw(f"Set Basic Salary Companent in Company")
		return basic