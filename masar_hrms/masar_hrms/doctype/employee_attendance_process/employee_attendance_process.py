# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe, datetime
from frappe.model.document import Document
from frappe.query_builder.functions import  Sum
from frappe import db , qb , get_doc , throw , _ , bold 
from frappe.utils import flt
from datetime import datetime, time, timedelta

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
				'hour_rate' : 0 ,
    			'shortage_hour_rate' : 0 , 
    			'earning_salary' : 0 
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
		shortage = self.get_shortage_salary(employee=employee)
		return {
			'basic_salary' : basic_salary[0][0] if basic_salary else 0  , 
			'hour_rate' : round(hour_rate , 3) , 
			'shortage_hour_rate' : shortage.get('shortage_hour_rate' , 0 ), 
			'earning_salary' : shortage.get('earning_salary' , 0 )
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
		self.calculate_shortage() 
		# self.calculate_leaves()
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
		self.create_additional_salary_for_overtime()
		self.create_additional_salary_for_shortage()
		# self.create_additional_salary_for_leaves()

	def create_additional_salary_for_overtime(self): 
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
			
	def get_salary_leaves(self):
		return frappe.db.sql(f"""
                SELECT sla.name , sla.shift_type , sla.leave_duration , sla.total_amount  , sla.salary_component
				FROM `tabShort Leave Application` sla 
				WHERE sla.leave_date BETWEEN '{self.from_date}' AND '{self.to_date}'
				AND sla.docstatus =1 AND sla.status = 'Approved'
				AND sla.employee = '{self.employee}'          
                    """, as_dict=True)
					
	def calculate_leaves(self):
		leaves , totals = self.get_salary_leaves() , 0 
		for l in leaves:
			self.append('leaves' , {
				'short_leave_application': l.get('name'),
				'shift_type': l.get('shift_type'),
    			'salary_component': l.get('salary_component'),
				'leave_duration': l.get('leave_duration'),
				'total_amount': l.get('total_amount')
			})
			totals += l.get('total_amount', 0)	
		self.total_leaves_amount = totals
  
  
	def create_additional_salary_for_leaves(self):
		if len(self.leaves) > 0:
			component_totals = {}
			for l in self.leaves:
				if l.total_amount != 0:
					component = l.salary_component
					component_totals.setdefault(component, 0)
					component_totals[component] += l.total_amount
			for component, total_amount in component_totals.items():
				frappe.new_doc('Additional Salary').update(
					frappe._dict({
						'employee': self.employee,
						'employee_name': self.employee_name,
						'department': self.department,
						'company': self.company,
						'is_recurring': 0,
						'payroll_date': self.to_date,
						'salary_component': component,
						'type': "Deduction",
						'amount': total_amount,
						'deduct_full_tax_on_selected_payroll_date': 1,
						'overwrite_salary_structure_amount': 1,
						'ref_doctype': self.doctype,
						'ref_docname': self.name
					})
				).insert().submit()

	def get_shortage_salary(self , employee = None): 
		if employee is None: 
			employee = self.employee
		if employee is None: 	
			return {
				'earning_salary' : 0 , 
				'shortage_hour_rate' : 0 
		}
		est = qb.DocType('Employee Salary Table')
		earning_salary = (
      		qb.from_(est)
        	.where(est.parent == employee)
         	.where(est.is_active == 1)
			.select(Sum(est.esc_amount))
   		).run()
		standard_working_hours = get_doc('HR Settings').standard_working_hours
		if standard_working_hours in [0 , None]: 
			standard_working_hours = 8 ###### if not define defualt is 8 hours
		shortage_hour_rate = float(
			flt( earning_salary[0][0] if earning_salary else 0) / 
			flt(standard_working_hours * self.number_of_day() )
		)
		return {
			'earning_salary' : earning_salary[0][0] if earning_salary else 0  , 
			'shortage_hour_rate' : round(shortage_hour_rate , 3)
		}

	def calculate_shortage(self):
		def to_time(value):
			"""Convert MariaDB TIME (timedelta) or already time object into datetime.time"""
			if isinstance(value, time):
				return value
			elif isinstance(value, timedelta):
				total_seconds = int(value.total_seconds())
				hours = (total_seconds // 3600) % 24
				minutes = (total_seconds % 3600) // 60
				seconds = total_seconds % 60
				return time(hour=hours, minute=minutes, second=seconds)
			return None

		self.leaves = []
		self.total_leaves_amount = 0
		salary_details = self.get_salary_details()
		self.earning_salary = flt(salary_details.get('earning_salary', 0))
		self.shortage_hour_rate = flt(salary_details.get('shortage_hour_rate', 0))
		if not self.employee or not self.from_date or not self.to_date:
			return

		hour_rate = self.get_shortage_salary().get('shortage_hour_rate', 0)
		attendance_data = self.get_attendance_for_shortage()
		short_leaves = self.get_short_leaves_in_period()

		for record in attendance_data:
			if record.is_off_day:
				continue

			late_shortage = 0
			early_shortage = 0

			shift_start_time = to_time(record.shift_start_time)
			shift_end_time = to_time(record.shift_end_time)

			shift_start_dt = datetime.combine(record.attendance_date, shift_start_time)
			shift_end_dt = datetime.combine(record.attendance_date, shift_end_time)    

			if record.enable_late_entry_marking and record.in_time:
				grace_start = shift_start_dt + timedelta(minutes=record.late_entry_grace_period)
				if record.in_time > grace_start:
					late_shortage = (record.in_time - shift_start_dt).total_seconds()

			if record.enable_early_exit_marking and record.out_time:
				grace_end = shift_end_dt - timedelta(minutes=record.early_exit_grace_period)
				if record.out_time < grace_end:
					early_shortage = (shift_end_dt - record.out_time).total_seconds()
			date_str = record.attendance_date.strftime('%Y-%m-%d')
			sla_name = None
			leave_duration = None
			if date_str in short_leaves:
			
				for sl in short_leaves[date_str]:
					sla_name = sl.sla_name
					leave_duration = sl.leave_duration
					sl_from_dt = datetime.combine(record.attendance_date, to_time(sl.from_time))
					sl_to_dt = datetime.combine(record.attendance_date, to_time(sl.to_time))
					if sl.salary_deduction:
						pass
					elif sl.balance_deduction:
						if late_shortage > 0:
							overlap = self.get_overlap_seconds(
								shift_start_dt, record.in_time, 
								sl_from_dt, sl_to_dt
							)
							late_shortage = max(0, late_shortage - overlap)
						if early_shortage > 0:
							overlap = self.get_overlap_seconds(
								record.out_time, shift_end_dt, 
								sl_from_dt, sl_to_dt
							)
							early_shortage = max(0, early_shortage - overlap)
			total_this_day = late_shortage + early_shortage
			amount_this_day = (total_this_day / 3600) * hour_rate
			if total_this_day > 0:
				self.append('leaves', {
					'attendance_date': record.attendance_date,
					'attendance': record.attendance,
					'shift_type': record.shift_type,
					'in_time' : record.in_time,
					'out_time' : record.out_time,
					'late_entry' : 1 if late_shortage  > 0 else 0 ,
					'early_exit' : 1 if  early_shortage > 0 else 0,
					'late_shortage': late_shortage,
					'early_shortage': early_shortage,
					'total_shortage': total_this_day,
					'amount': amount_this_day , 
					'short_leave_application': sla_name if sla_name else None,
					'leave_duration': leave_duration if leave_duration else None
				})
				self.total_shortage_amount =flt(self.total_shortage_amount) + flt(amount_this_day)
				self.total_shortage =flt(self.total_shortage)  + flt(total_this_day)


	def get_overlap_seconds(self, start1, end1, start2, end2):
		"""Calculate overlap in seconds between two time periods"""
		latest_start = max(start1, start2)
		earliest_end = min(end1, end2)
		if latest_start < earliest_end:
			return (earliest_end - latest_start).total_seconds()
		return 0

	def get_attendance_for_shortage(self):
		"""Fetch attendance data with shift details"""
		sql = """
			SELECT 
				a.name AS attendance,
				a.attendance_date,
				a.in_time,
				a.out_time,
				sa.shift_type,
				st.start_time AS shift_start_time,
				st.end_time AS shift_end_time,
				st.enable_late_entry_marking AS enable_late_entry_marking,
				st.late_entry_grace_period AS late_entry_grace_period,
				st.enable_early_exit_marking AS enable_early_exit_marking,
				st.early_exit_grace_period AS early_exit_grace_period,
				IF(h.name IS NOT NULL, 1, 0) AS is_off_day
			FROM `tabAttendance` a
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
				a.employee = %(employee)s
				AND a.attendance_date BETWEEN %(from_date)s AND %(to_date)s
		"""
		return frappe.db.sql(sql, {
			'employee': self.employee,
			'from_date': self.from_date,
			'to_date': self.to_date
		}, as_dict=True)

	def get_short_leaves_in_period(self):
		"""Get approved short leaves grouped by date"""
		sql = """
			SELECT 
				name as sla_name,
				leave_date,
				from_time,
				to_time,
				leave_duration,
				balance_deduction,
				salary_deduction
			FROM `tabShort Leave Application`
			WHERE 
				employee = %(employee)s
				AND leave_date BETWEEN %(from_date)s AND %(to_date)s
				AND docstatus = 1
				AND status = 'Approved'
		"""
		short_leaves = frappe.db.sql(sql, {
			'employee': self.employee,
			'from_date': self.from_date,
			'to_date': self.to_date
		}, as_dict=True)
		
		result = {}
		for sl in short_leaves:
			date_str = sl.leave_date.strftime('%Y-%m-%d')
			if date_str not in result:
				result[date_str] = []
			result[date_str].append(sl)
		return result

	def create_additional_salary_for_shortage(self):
		"""Create deduction for total shortage amount"""
		if self.total_shortage_amount > 0:
			frappe.get_doc({
				'doctype': 'Additional Salary',
				'employee': self.employee,
				'employee_name': self.employee_name,
				'department': self.department,
				'company': self.company,
				'payroll_date': self.to_date,
				'salary_component': self.shortage_salary_component,
				'amount': self.total_shortage_amount,
				'type': 'Deduction',
				'ref_doctype': self.doctype,
				'ref_docname': self.name
			}).insert().submit()