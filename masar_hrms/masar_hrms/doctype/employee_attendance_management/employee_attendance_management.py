# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta, datetime
from frappe.model.document import Document


class EmployeeAttendanceManagement(Document):
	def on_submit(self):
		self.additional_salary_for_overtime()
		# self.additional_salary_for_leaves()
	def validate(self):
		self.validate_date()
		self.calc_overtime_rate()
		# self.calculate_leaves_rate()
    

	def validate_date(self):
		if not self.from_date or not self.to_date:
			frappe.throw("Please set the from and to dates.")
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw("'From Date' can't be later than 'To Date'.")
   
	def additional_salary_for_overtime(self):
		if self.total_wd or self.total_od:
			salary_components = {}
			if self.total_wd:
				if self.sc_overtime_wd in salary_components:
					salary_components[self.sc_overtime_wd] += float(self.total_wd)
				else:
					salary_components[self.sc_overtime_wd] = float(self.total_wd)	
			if self.total_od:
				if self.sc_overtime_od in salary_components:
					salary_components[self.sc_overtime_od] += float(self.total_od)
				else:
					salary_components[self.sc_overtime_od] = float(self.total_od)
			for salary_component, total in salary_components.items():
				additional_salary = frappe.new_doc('Additional Salary')
				additional_salary.employee = self.employee
				additional_salary.employee_name = self.employee_name
				additional_salary.department = self.department
				additional_salary.company = self.company
				additional_salary.is_recurring = 0
				additional_salary.payroll_date = self.to_date
				additional_salary.salary_component =  salary_component
				additional_salary.type  = "Deduction"
				additional_salary.amount =  total
				additional_salary.deduct_full_tax_on_selected_payroll_date = 1
				additional_salary.overwrite_salary_structure_amount = 1
				additional_salary.ref_doctype = self.doctype
				additional_salary.ref_docname = self.name
				additional_salary.insert(ignore_permissions=True)
				additional_salary.submit()
				if salary_component == self.sc_overtime_wd and self.total_wd != 0 :
					self.add_sal_wd = additional_salary.name
				if salary_component == self.sc_overtime_od and self.total_od != 0 :
					self.add_sal_od = additional_salary.name
				frappe.msgprint("The Additional Salary for Overtime has been Successfully Created.", alert=True, indicator='green')
		else:
			frappe.msgprint("No Additional Salary for Overtime Records Were Found.", alert=True, indicator='blue')
    
	def calc_overtime_rate(self):
		if self.doctype == 'Employee Attendance Management':
			self.get_salary_component()
		amount_wd , amount_od = 0, 0
		data_salary = self.get_hours_rate_and_salaries()
		working_day = data_salary.working_day
		basic_salary =  data_salary.basic_salary 
		basic_salary_hour_rate = data_salary.basic_salary_hour_rate
		overtime_data = self.calculate_employee_overtime()
		if overtime_data:
			working_day_in_seconds = overtime_data.ot_working_day
			off_day_in_seconds = overtime_data.ot_off_day
			if self.overtime_type_wd:
				self.overtime_wd = working_day_in_seconds
				amount_wd = float(basic_salary_hour_rate) * (float(working_day_in_seconds)/3600) * float(self.overtime_rate_wd)
			if self.overtime_type_od:
				self.overtime_od = off_day_in_seconds
				amount_od = float(basic_salary_hour_rate) * (float(off_day_in_seconds)/3600) * float(self.overtime_rate_od)
			self.amount_wd = amount_wd
			self.amount_od = amount_od
			self.working_day = int(working_day)
			self.basic_salary = basic_salary
			self.bs_hour_rate = basic_salary_hour_rate
			self.total_wd = amount_wd
			self.total_od = amount_od
			self.ot_total_amount = float(amount_wd + amount_od)
    
	def get_salary_component(self):
		ot = frappe.qb.DocType('Overtime Type')
		sc = (
			frappe.qb.from_(ot)
			.select(
       			(ot.name),
				(ot.rate),
				(ot.salary_component),
			)
		)
		sc_wd = sc.where(ot.working_day == 1).run(as_dict = True)				
		if sc_wd and sc_wd[0] and sc_wd[0]['name']:
			self.overtime_type_wd = sc_wd[0]['name']
			self.overtime_rate_wd = sc_wd[0]['rate']
			self.sc_overtime_wd = sc_wd[0]['salary_component']
		else: 
			frappe.throw('Set Overtime Type where Type is Normal Day')
		sc_od = sc.where(ot.off_day == 1).run(as_dict = True)
		if sc_od and sc_od[0] and sc_od[0]['name']:
			self.overtime_type_od = sc_od[0]['name']
			self.overtime_rate_od = sc_od[0]['rate']
			self.sc_overtime_od = sc_od[0]['salary_component']
		else: 
			frappe.throw('Set Overtime Type where Type is Off Day')
		return 1 

	@frappe.whitelist()
	def get_hours_rate_and_salaries(self):
		number_of_payment_days = self.get_number_of_days()
		salaries = self.get_basic_salary_and_basic_salry_with_allowance()
		if self.employee:
			employee_doc = frappe.get_doc("Employee", self.employee)
			if employee_doc.default_shift:
				shift_type_doc = frappe.get_doc("Shift Type" ,  employee_doc.default_shift)
				start_time = shift_type_doc.start_time
				end_time = shift_type_doc.end_time
				time_duration_str = str(end_time - start_time)
				time_duration = datetime.strptime(time_duration_str, "%H:%M:%S")
				hours = time_duration.hour
				minutes = time_duration.minute
				number_of_hours = hours + minutes / 60
				basic_salary = salaries.basic_salary
				basic_salary_in_hour = basic_salary / number_of_hours
				bs_hour_rate = round(float(basic_salary_in_hour) / float(number_of_payment_days) , 3)
				self.working_day = int(number_of_payment_days)
				self.basic_salary = basic_salary
				self.bs_hour_rate = bs_hour_rate
				dict_ =  frappe._dict(
					{
					"working_day": number_of_payment_days,
					"basic_salary": basic_salary, 
					"basic_salary_hour_rate": bs_hour_rate,
					}
				)
				return dict_
			else:
				frappe.throw(f"Self Employee Default Shift for Employee: {self.employee}")
		else:
			frappe.throw("Set Employee")
   
	@frappe.whitelist()
	def get_number_of_days(self):
		if self.employee and self.posting_date and self.from_date and self.to_date:
			payroll_settings = frappe.get_doc('Payroll Settings')
			employee_doc = frappe.get_doc('Employee' , self.employee)
			if employee_doc.default_shift:
				if payroll_settings.include_holidays_in_total_working_days:
					from_date_obj = datetime.strptime(str(self.from_date), '%Y-%m-%d').date()
					to_date_obj = datetime.strptime(str(self.to_date), '%Y-%m-%d').date()
					number_of_days_full_period = (to_date_obj - from_date_obj).days + 1
					return number_of_days_full_period
			else:
				frappe.throw(f"Set Employee Default Shift for Employee: {self.employee}.")
		else:
			frappe.throw("Set Employee or dates.")
   
	@frappe.whitelist()
	def get_basic_salary_and_basic_salry_with_allowance(self):
		basic_salary = 0
		if self.employee and self.posting_date and self.from_date and self.to_date:
			employee_doc = frappe.get_doc("Employee" , self.employee )
			company_doc = frappe.get_doc("Company" , self.company)
			basic_sc = company_doc.custom_basic_salary_component
			if basic_sc in [None , '' , ' ']:
				frappe.throw(f"Set Default Basic Salary in Company {str(self.comany)}")
			for esc in employee_doc.custom_salary_component_table:
				if esc.is_active:
					sal_comp_doc = frappe.get_doc("Salary Component", esc.salary_component)
					if esc.salary_component == basic_sc or sal_comp_doc.is_overtime_applicable:
						basic_salary += esc.esc_amount
			return frappe._dict({
					"basic_salary" : basic_salary
				})
		else:
			frappe.throw("Set Employee and Posting Date")

	def calculate_employee_overtime(self):
		self.overtime_details = []
		over_time_wd_in_seconds = 0
		over_time_od_in_seconds = 0 
		if self.posting_date and self.to_date and self.from_date and self.employee:
			emp_doc = frappe.get_doc("Employee" , self.employee)
			is_overtime_applicable = emp_doc.is_overtime_applicable
			if is_overtime_applicable == 0 :
				frappe.msgprint(_(f"Employee: {self.employee} is not Eligible for Overtime"))
				return False
			attendance_sql = frappe.db.sql("""
				SELECT 
					ta.name,
					ta.employee,
					ta.employee_name,
					ta.department,
					ta.attendance_date,
					ta.in_time,
					ta.out_time,
					tst.start_time,
					tst.end_time,
					tst.holiday_list
				FROM 
					`tabAttendance` ta
				INNER JOIN 
					`tabShift Type` tst ON tst.name = ta.shift
				INNER JOIN 
					`tabEmployee` te ON te.name = ta.employee
				WHERE 
					te.is_overtime_applicable = 1 
					AND ta.status = 'Present' 
					AND ta.employee = %s 
					AND ta.attendance_date BETWEEN %s AND %s
			""", (self.employee, self.from_date, self.to_date,), as_dict=True)
			if len(attendance_sql) != 0 :
				for att in attendance_sql:
					employee = att.employee
					employee_name = att.employee_name
					department = att.department
					attendance_date = att.attendance_date
					in_time = att.in_time
					out_time = att.out_time
					start_time= att.start_time
					end_time = att.end_time
					holiday_list_att = att.holiday_list
					start_seconds = start_time.total_seconds()
					end_seconds = end_time.total_seconds()
					start_of_day = datetime.combine(attendance_date, datetime.min.time())
					in_time_seconds = (in_time - start_of_day).total_seconds()
					out_time_seconds = (out_time - start_of_day).total_seconds()
					overtime_start_seconds = start_seconds
					overtime_end_seconds = end_seconds
					holiday_list = []
					holiday_date_sql = self.holiday_date_in_period( 
							shift_name = holiday_list_att , 
							start_date = self.from_date , 
							end_date = self.to_date 
					)
					att_date = datetime.strptime(str(attendance_date), '%Y-%m-%d').date()
					for holiday_date in holiday_date_sql:
						holiday_list.append(holiday_date.holiday_date)
					employee_overtime_before_shift_seconds = 0 
					employee_overtime_after_shift_seconds = 0 
					if att_date in holiday_list:
						day_time_in_seconds = out_time_seconds - in_time_seconds
						over_time_od_in_seconds += day_time_in_seconds
						self.append('overtime_details',{
							'attendance' : att.name , 
							"employee":employee,
							'employee_name': employee_name,
							'department': department,
							'time_in':in_time,
							'time_out':out_time,
							"overtime":day_time_in_seconds ,
							"attendance_date":attendance_date,
							'off_day': 1
							})
					else: 
						if in_time_seconds < overtime_start_seconds:
							employee_overtime_before_shift_seconds = overtime_start_seconds - in_time_seconds
						if out_time_seconds > overtime_end_seconds:
							employee_overtime_after_shift_seconds = out_time_seconds - overtime_end_seconds
						if employee_overtime_after_shift_seconds + employee_overtime_before_shift_seconds > 0 :
							employee_overtime_in_day_seconds = employee_overtime_after_shift_seconds + employee_overtime_before_shift_seconds
						over_time_wd_in_seconds +=  employee_overtime_in_day_seconds
						self.append('overtime_details',{
									'attendance' : att.name , 
									"employee":employee,
									'employee_name': employee_name,
									'department': department,
									'time_in':in_time,
									'time_out':out_time,
									"overtime":employee_overtime_in_day_seconds ,
									"attendance_date":attendance_date,
									'working_day': 1
									})
				overtime = frappe._dict({
					'ot_working_day' : over_time_wd_in_seconds , 
					'ot_off_day' :over_time_od_in_seconds,
				})
				return overtime
		else:
			frappe.throw("Set Employee and Posting Date")
   
	def holiday_date_in_period(self , shift_name , start_date , end_date ):
		if shift_name and start_date and end_date:
			h = frappe.qb.DocType('Holiday')
			holiday_dict = (
				frappe.qb.from_(h)
				.select(
					(h.holiday_date), 
					(h.weekly_off )
					)
				.where(h.parent == shift_name)
				.where(h.holiday_date.between(start_date , end_date))
				.orderby(h.idx)
			).run(as_dict = True)
			return holiday_dict
		else:
			return None
   
	# def get_leaves_salary_and_leaves_hour_rate(self):
	# 	leaves_salary = self.calculate_leaves_salary()
	# 	number_of_payment_days = self.get_number_of_days()
	# 	if self.employee:
	# 		employee_doc = frappe.get_doc('Employee' , self.employee)
	# 		if employee_doc.default_shift:
	# 			shift_type_doc = frappe.get_doc('Shift Type' ,  employee_doc.default_shift)
	# 			start_time = shift_type_doc.start_time
	# 			end_time = shift_type_doc.end_time
	# 			time_duration_str = str(end_time - start_time)
	# 			time_duration = datetime.strptime(time_duration_str, "%H:%M:%S")
	# 			hours = time_duration.hour
	# 			minutes = time_duration.minute
	# 			number_of_hours = hours + minutes / 60
	# 			leaves_hour_rate = (float(leaves_salary) / float(number_of_hours)) / float(number_of_payment_days)
	# 			leaves_dict = frappe._dict({
	# 				'leaves_salary': leaves_salary , 
	# 				'leaves_hour_rate' : leaves_hour_rate
	# 			})
	# 			return leaves_dict
	# 		else:
	# 			frappe.throw(f"Self Employee Default Shift for Employee: {self.employee}")
	# 	else:
	# 		frappe.throw("Set Employee")

   
	# def calculate_leaves_salary(self):
	# 	basic_salary, leaves_salary, leaves_salary_comp = 0, 0, 0 
	# 	sc_basic = []
	# 	if self.employee and self.posting_date and self.from_date and self.to_date:
	# 		from_date = datetime.strptime(str(self.from_date), '%Y-%m-%d').date()
	# 		to_date = datetime.strptime(str(self.to_date), '%Y-%m-%d').date()
	# 		employee_doc = frappe.get_doc('Employee' , self.employee )
	# 		company_doc = frappe.get_doc('Company' , self.company)
	# 		sc_basic.append(company_doc.custom_basic_salary_component)
	# 		if len(sc_basic) == 0:
	# 			frappe.throw(f"Set Default Basic Salary in Company {str(self.comany)}")
	# 		basic_in_table = None
	# 		for esc in employee_doc.custom_salary_component_table:
	# 			if esc.salary_component in sc_basic and esc.is_active:
	# 				basic_in_table = esc.salary_component
	# 				basic_salary = esc.esc_amount
	# 			if esc.is_active and (from_date <= datetime.strptime(str(esc.date), '%Y-%m-%d').date() <= to_date):
	# 				if esc.salary_component != basic_in_table:
	# 					sal_comp_doc = frappe.get_doc('Salary Component' ,esc.salary_component )
	# 					if sal_comp_doc.custom_is_short_leave_applicable:
	# 						leaves_salary_comp += esc.esc_amount
	# 		leaves_salary = leaves_salary_comp + basic_salary
	# 		return leaves_salary
	# 	else:
	# 		frappe.throw("Set Employee or Posting Date.")
 
		# def calculate_leaves_rate(self):
	# 	leave = self.get_leaves_salary_and_leaves_hour_rate()
	# 	leaves_salary = leave.leaves_salary
	# 	leaves_hour_rate = leave.leaves_hour_rate
	# 	if self.posting_date:
	# 		if self.from_date and self.to_date:
	# 			from_date = self.from_date 
	# 			to_date = self.to_date
	# 		sla_sql = frappe.db.sql("""
    #             SELECT
	# 				tsla.name,
	# 				tsla.salary_component,
	# 				tsla.leave_type,
	# 				tsla.leave_date,
	# 				tsla.from_time,
	# 				tsla.leave_duration,
	# 				tsla.to_time,
	# 				tlt.custom_salary_deduction_rate
	# 			FROM `tabShort Leave Application` tsla
	# 			INNER JOIN `tabLeave Type` tlt ON tlt.name = tsla.leave_type
	# 			WHERE 
    # 				tsla.docstatus = 1 
    #     			AND tsla.status = 'Approved' 
    #        			AND tsla.leave_date BETWEEN %s AND %s
	# 		""", (from_date, to_date,), as_dict=True)
	# 		total_amount = 0 
	# 		self.leaves_table = []
	# 		if len(sla_sql) != 0 :
	# 			for sla in sla_sql:
	# 				amount_row =  round(float(sla.custom_salary_deduction_rate) * float(leaves_hour_rate) * (sla.leave_duration /3600) , 3)
	# 				total_amount+=amount_row
	# 				self.append('leaves_table' , {
	# 					'short_leave_application' : sla.name, 
	# 					'salary_component' : sla.salary_component , 
	# 					'leave_type' : sla.leave_type , 
	# 					'leave_date' : sla.leave_date , 
	# 					'from_time' : sla.from_time , 
	# 					'leave_duration': sla.leave_duration , 
	# 					'to_time': sla.to_time , 
	# 					'salary_deduction_rate': sla.custom_salary_deduction_rate , 
	# 					'leave_hour_rate': leaves_hour_rate , 
	# 					'amount' : amount_row
	# 				})
	# 		else : 
	# 			total_amount = 0 
	# 		self.leaves_salary = leaves_salary
	# 		self.leaves_hour_rate = leaves_hour_rate
	# 		self.total_amount = total_amount
 
	# def additional_salary_for_leaves(self):
	# 	if self.total_amount:
	# 		add_sal_leaves_sql = frappe.db.sql("""
	# 				SELECT SUM(amount) AS amount, salary_component
	# 				FROM `tabEmployee Attendance Management Leaves`
	# 				WHERE parent = %s
	# 				GROUP BY salary_component
	# 		""" , (self.name) , as_dict = True)
	# 		if len (add_sal_leaves_sql) != 0 :
	# 			for add_sal in add_sal_leaves_sql:
	# 				additional_salary = frappe.new_doc('Additional Salary')
	# 				additional_salary.employee = self.employee
	# 				additional_salary.employee_name = self.employee_name
	# 				additional_salary.department = self.department
	# 				additional_salary.company = self.company
	# 				additional_salary.is_recurring = 0
	# 				additional_salary.payroll_date = self.to_date
	# 				additional_salary.salary_component =  add_sal.salary_component
	# 				additional_salary.type  = "Deduction"
	# 				additional_salary.amount =  add_sal.amount
	# 				additional_salary.deduct_full_tax_on_selected_payroll_date = 1
	# 				additional_salary.overwrite_salary_structure_amount = 1
	# 				additional_salary.ref_doctype = self.doctype
	# 				additional_salary.ref_docname = self.name
	# 				additional_salary.insert(ignore_permissions=True)
	# 				additional_salary.submit()
	# 			frappe.msgprint("The Additional Salary for Leaves has been Successfully Created.", alert=True, indicator='green')
	# 	else:
	# 		frappe.msgprint("No Additional Salary for Leaves Records Were Found.", alert=True, indicator='blue')