# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta, datetime
from frappe.model.document import Document


class EmployeeAttendanceManagementBulk(Document):
	def validate(self):
		self.validate_date()
	def on_submit(self):
		self.create_attendance_management()
  
	
	def validate_date(self):
		if not self.from_date or not self.to_date:
			frappe.throw("Please set the from and to dates.")
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw("'From Date' can't be later than 'To Date'.")
	
	def create_attendance_management(self):
		posting_date = str(self.posting_date)
		
		if not self.employees:
			frappe.throw("No employees found.")
		for emp in self.employees:
			if emp.default_shift:
				new_eam = frappe.new_doc("Employee Attendance Management")
				new_eam.employee = emp.employee
				new_eam.employee_name = emp.employee_name
				new_eam.department = emp.department
				new_eam.from_date = self.from_date
				new_eam.to_date = self.to_date
				new_eam.posting_date = posting_date
				new_eam.company = self.company
				new_eam.eamb_ref = self.name
				new_eam.insert()
		

	@frappe.whitelist()
	def get_employees(self):
		self.employees = []
		cond = " 1=1"
		if self.department:
			cond += f" AND te.department = '{self.department}'"
		if self.default_shift:
			cond  += f" AND te.default_shift = '{self.default_shift}'" 
   
		employees = frappe.db.sql(f"""
                SELECT 
                	te.name, 
                 	te.employee_name, 
                  	te.department, 
                   	te.designation, 
                    te.nationality , 
                    te.default_shift 
                FROM `tabEmployee` te 
                WHERE {cond}
            """ , as_dict=True)	
		if not employees:
			frappe.throw("No employees found in the given filters.")
		for employee in employees:
			self.append('employees',{
				'employee' :employee.name,
				'employee_name' : employee.employee_name,
				'department' : employee.department,
				"designation": employee.designation,
				'nationality': employee.nationality,
				'default_shift':employee.default_shift
			})
		return True


	@frappe.whitelist()	
	def submit_all_attendance_managements(self):
		attendance_management = frappe.db.sql("SELECT name FROM `tabEmployee Attendance Management` WHERE eamb_ref = %s" , (self.name) , as_dict = True )
		without_ssa = list()
		
		for ap in attendance_management:
			doc = frappe.get_doc('Employee Attendance Management', ap.name)
			ssa_sql = frappe.db.sql("""SELECT name FROM `tabSalary Structure Assignment` tssa WHERE tssa.employee = %s  
                           AND tssa.from_date < %s AND tssa.docstatus = 1""" , (doc.employee , self.from_date  ) , as_dict= True)
			if not (ssa_sql and ssa_sql[0] and ssa_sql[0]['name']):
				without_ssa.append(doc.employee)
			else:
				doc.run_method("submit")
		msg2=''
		if len(without_ssa) != 0 :
			msg2+=" Bulk Not Submitted For Employees Without Salary Structure Assignment, are: <br> <ul>"
			for ssa in without_ssa:
				msg2+=f'<li> Employee: <b> {ssa} </b> </li>'
			msg2+='</ul>'
		if msg2:	
			frappe.msgprint(msg2)