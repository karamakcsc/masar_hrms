# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe, datetime
from datetime import timedelta , datetime
from frappe.model.document import Document
from frappe import db , qb , get_doc , throw , _ , bold 

class EmployeeAttendanceProcess(Document):
	def number_of_day(self):
		return 30 
	def get_basic_salary_component(self): 
		basic = db.get_value('Company' , self.company , 'custom_basic_salary_component')
		if basic is None:
			throw(f"Set Basic Salary Companent in Company")
		return basic
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
	def get_overtime_type_as_defualt(self): 
		ot = qb.DocType('Overtime Type')
		working_day_result = qb.from_(ot).select(ot.name , ot.salary_component , ot.rate).where(ot.working_day == 1).run()
		if len(working_day_result) == 1: 
			self.ot_wd = working_day_result[0][0]
			self.salary_component_wd =  working_day_result[0][1]
			self.ot_wd_rate =  working_day_result[0][2]
		off_day_reuslt =  qb.from_(ot).select(ot.name , ot.salary_component , ot.rate).where(ot.off_day == 1).run()
		if len(off_day_reuslt) == 1: 
			self.ot_od = off_day_reuslt[0][0]
			self.salary_component_od =  off_day_reuslt[0][1]
			self.ot_od_rate =  off_day_reuslt[0][2]
		return { 
          'ot_wd' : self.ot_wd , 
          'salary_component_wd' : self.salary_component_wd , 
          'ot_wd_rate' : self.ot_wd_rate , 
          'ot_od' : self.ot_od , 
          'salary_component_od' : self.salary_component_od , 
          'ot_od_rate' : self.ot_od_rate
          }
	def validate(self): 
		self.employee_validate()
		self.date_validate()
		self.calculate_overtime()
	def employee_validate(self): 
		basic_salary = self.get_salary_details()['basic_salary']
		if basic_salary in [0 , None]: 
			throw(_(f"Employee {bold(self.employee)} must have an active Basic Salary component."))
		if not db.get_value('Employee' , self.employee , 'is_overtime_applicable'): 
			throw(_(f"Employee {bold(self.employee)} must be marked as overtime applicable."))
   
	def date_validate(self): 
		if not (self.from_date <= self.posting_date <= self.to_date): 
			throw(_(f"Posting Date must be within the period between {bold(self.from_date)} and {bold(self.to_date)}."))
		overlapping = frappe.db.exists(
        	self.doctype,
			{
				"employee": self.employee,
				"name": ["!=", self.name], 
				"docstatus": ["!=", 2], 
				"from_date": ["<=", self.to_date],
				"to_date": [">=", self.from_date],
			}
		)
		if overlapping:
			throw(_(f"An overlapping record already exists for Employee {bold(self.employee)} within the period {bold(self.from_date)} to {bold(self.to_date)}."))
   
	def calculate_overtime(self):
		def get_data_for_overtime():
			return frappe.db.sql(f"""
					SELECT 
						a.name AS attendance , 
						a.employee,
						a.employee_name, 
						a.attendance_date,
						a.in_time,
						a.out_time,
						sa.start_date,
						sa.end_date,
						sa.shift_type,
						st.start_time,
						st.end_time,
						st.custom_early_entry_grace_period,
						st.custom_late_exit_grace_period,
						st.custom_enable_early_entry_marking,
						st.custom_enable_late_exit_marking,
						IF(
							st.custom_enable_early_entry_marking = 1 
							AND a.in_time < (
								TIMESTAMP(CONCAT(a.attendance_date, ' ', st.start_time)) - INTERVAL st.custom_early_entry_grace_period MINUTE
							),
							TIMESTAMPDIFF(
								SECOND, 
								a.in_time, 
								TIMESTAMP(CONCAT(a.attendance_date, ' ', st.start_time)) 
        						-- - INTERVAL st.custom_early_entry_grace_period MINUTE
							),
							0
						) AS early_entry_overtime_seconds,
						IF(
							st.custom_enable_late_exit_marking = 1 
							AND a.out_time > (
								TIMESTAMP(CONCAT(a.attendance_date, ' ', st.end_time)) + INTERVAL st.custom_late_exit_grace_period MINUTE
							),
							TIMESTAMPDIFF(
								SECOND, 
								TIMESTAMP(CONCAT(a.attendance_date, ' ', st.end_time)) 
        						-- + INTERVAL st.custom_late_exit_grace_period MINUTE
              					, a.out_time
							),
							0
						) AS late_exit_overtime_seconds,
						IF(h.name IS NOT NULL, 1, 0) AS is_off_day,
						IF(h.name IS NOT NULL AND a.in_time IS NOT NULL AND a.out_time IS NOT NULL,
							TIMESTAMPDIFF(SECOND, a.in_time, a.out_time),
							0
						) AS off_day_time_seconds
					FROM 
						tabAttendance a
					INNER JOIN `tabShift Assignment` sa 
						ON sa.employee = a.employee 
						AND a.attendance_date BETWEEN sa.start_date AND sa.end_date 
						AND sa.status = 'Active' 
						AND sa.docstatus = 1 
					INNER JOIN `tabShift Type` st 
						ON sa.shift_type = st.name
					LEFT JOIN `tabHoliday List` hl 
						ON hl.name = st.holiday_list
					LEFT JOIN `tabHoliday` h 
						ON h.parent = hl.name 
						AND h.holiday_date = a.attendance_date
							WHERE 
						a.employee = '{self.employee}'
						AND a.attendance_date BETWEEN '{str(self.from_date)}' AND '{str(self.to_date)}'
					ORDER BY a.attendance_date
			""", as_dict=True)
		data , off_duration , working_duration = get_data_for_overtime() , 0 , 0
		self.overtime_table = list()
		overtime_ceiling_hours = frappe.db.get_value('Employee', self.employee, 'overtime_ceiling') or 0
		ceiling_seconds = overtime_ceiling_hours * 3600
		accumulated_overtime = 0 
		for d in sorted(data, key=lambda x: x['attendance_date']):
			daily_overtime = 0
			if d.is_off_day == 0 and (d.early_entry_overtime_seconds > 0 or d.late_exit_overtime_seconds > 0):
				daily_overtime = d.early_entry_overtime_seconds + d.late_exit_overtime_seconds
			elif d.is_off_day == 1 and d.off_day_time_seconds > 0:
				daily_overtime = d.off_day_time_seconds
			if accumulated_overtime < ceiling_seconds:
				allowable_overtime = min(daily_overtime, ceiling_seconds - accumulated_overtime)
				accumulated_overtime += allowable_overtime
				if allowable_overtime > 0:
					row = {
						'employee': d.employee,
						'employee_name': d.employee_name,
						'attendance': d.attendance,
						'attendance_date': d.attendance_date,
						'off_day': 1 if d.is_off_day else 0,
						'working_day': 0 if d.is_off_day else 1,
						'time_in': d.in_time,
						'time_out': d.out_time,
						'overtime': allowable_overtime 
					}
					self.append('overtime_table', row)
					if d.is_off_day:
						off_duration += allowable_overtime
					else:
						working_duration += allowable_overtime
		salary_details = self.get_salary_details()
		hour_rate = salary_details.get('hour_rate', 0)
		self.ot_wd_time = working_duration
		self.ot_od_time = off_duration
		self.ot_wd_amount = round(float((working_duration / 3600) * self.ot_wd_rate * hour_rate), 3)
		self.ot_od_amount = round(float((off_duration / 3600) * self.ot_od_rate * hour_rate), 3)
		self.working_day_amount = self.ot_wd_amount
		self.off_day_amount = self.ot_od_amount
		self.total_amount = self.ot_od_amount + self.ot_wd_amount
		
	def on_submit(self): 
		self.employee_validate()
		self.date_validate()
		self.crate_additional_salary()
  
  
	def crate_additional_salary(self): 
		if self.salary_component_wd  == self.salary_component_od and self.total_amount != 0  :
			frappe.new_doc('Additional Salary').update(
			frappe._dict({
				'employee' :  self.employee, 
				'employee_name' : self.employee_name,
				'department' : self.department,
				'company' : self.company,
				'is_recurring' :  0,
				'payroll_date' : self.to_date,
				'salary_component' :  self.salary_component_od,
				'type' : "Deduction",
				'amount' :  self.total_amount,
				'deduct_full_tax_on_selected_payroll_date' :  1,
				'overwrite_salary_structure_amount' :  1,
				'ref_doctype' : self.doctype,
				'ref_docname' : self.name
			})
			).insert().submit()
		else: 
			if self.ot_wd_amount !=0: 
				frappe.new_doc('Additional Salary').update(
				frappe._dict({
					'employee' :  self.employee, 
					'employee_name' : self.employee_name,
					'department' : self.department,
					'company' : self.company,
					'is_recurring' :  0,
					'payroll_date' : self.to_date,
					'salary_component' :  self.salary_component_wd,
					'type' : "Deduction",
					'amount' :  self.ot_wd_amount,
					'deduct_full_tax_on_selected_payroll_date' :  1,
					'overwrite_salary_structure_amount' :  1,
					'ref_doctype' : self.doctype,
					'ref_docname' : self.name
				})
				).insert().submit()
			if self.ot_od_amount != 0 :
				frappe.new_doc('Additional Salary').update(
				frappe._dict({
					'employee' :  self.employee, 
					'employee_name' : self.employee_name,
					'department' : self.department,
					'company' : self.company,
					'is_recurring' :  0,
					'payroll_date' : self.to_date,
					'salary_component' :  self.salary_component_od,
					'type' : "Deduction",
					'amount' :  self.ot_od_amount,
					'deduct_full_tax_on_selected_payroll_date' :  1,
					'overwrite_salary_structure_amount' :  1,
					'ref_doctype' : self.doctype,
					'ref_docname' : self.name
				})
				).insert().submit()
			

					
			
		


			
