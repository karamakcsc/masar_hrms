# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_weekday, add_days, formatdate
from frappe import db, enqueue, msgprint, _ , qb
from datetime import timedelta


class EmployeeShiftManagementBulk(Document):
	@frappe.whitelist()
	def get_day_by_date(self, date=None): 
		if date is None: 
			return None 
		date_obj = getdate(date)
		day_name = get_weekday(date_obj)
		return day_name
        
	@frappe.whitelist()
	def insert_shifts_periods(self): 
		if not (self.start_date and self.end_date):
			frappe.throw("Start Date and End Date are required")

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		if start_date > end_date:
			frappe.throw("End Date cannot be before Start Date")

		self.set("shifts_period", [])

		weekday_field_map = {
			0: "monday_st",    
			1: "tuesday_st",  
			2: "wednesday_st",  
			3: "thursday_st", 
			4: "friday_st",    
			5: "saturday_st",  
			6: "sunday_st"     
		}
		current_date = start_date
		while current_date <= end_date:
			weekday = current_date.weekday()
			shift_field = weekday_field_map.get(weekday)
			if shift_field:
				shift_type = self.get(shift_field)
				if shift_type:
					self.append("shifts_period", {
						"shift_date": current_date,
						"shift_day": current_date.strftime("%A"),
						"shift_type": shift_type, 
						"start_time": db.get_value('Shift Type', shift_type, 'start_time'), 
						"end_time": db.get_value('Shift Type', shift_type, 'end_time')
					})
			current_date = add_days(current_date, 1)
		msg = f"Created {len(self.shifts_period)} shift period(s) between {formatdate(self.start_date)} and {formatdate(self.end_date)}"
		msgprint(msg, alert=True, indicator='green')

	@frappe.whitelist()
	def insert_employees(self): 
		e = qb.DocType('Employee')
		employees = (
      		qb.from_(e).select(e.name , e.employee_name , e.department , e.designation )
			.where(e.status == 'Active')
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

	def validate(self): 
		self.validate_period_in_dates()
        
	def on_submit(self):
		self.create_employee_shift_management()
	def validate_period_in_dates(self): 
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		shift_dates = set()
		for s in self.shifts_period: 
			shift_date = getdate(s.shift_date)
			if not (start_date <= shift_date <= end_date):
				frappe.throw(
                    f"Row {s.idx}: Shift Date {shift_date} not in period between {start_date} and {end_date}"
                )
			if shift_date in shift_dates:
				frappe.throw(
                    f"Duplicate shift date found in Row {s.idx}: {shift_date}"
                )
			shift_dates.add(shift_date)
		current = start_date
		while current <= end_date:
			if current not in shift_dates:
				frappe.throw(
                    f"Missing shift on {current.strftime('%Y-%m-%d')}. All dates must be covered without gaps."
                )
			current += timedelta(days=1)

	def create_employee_shift_management(self):
		for e in self.employees: 
			args = {
				'employee': e.employee, 
				'employee_name' : e.employee_name , 
				'department' : e.department,
				'posting_date' : self.posting_date,
				'start_date' : self.start_date, 
				'end_date' : self.end_date,
				'bulk_ref': self.name,
				'saturday_st' : self.saturday_st, 
				'sunday_st' : self.sunday_st, 
				'monday_st' : self.monday_st, 
				'tuesday_st' : self.tuesday_st, 
				'wednesday_st' : self.wednesday_st,
				'thursday_st' : self.thursday_st,
				'friday_st' : self.friday_st,
				'shifts_period' :  self.shifts_period
			}
			esm = frappe.new_doc('Employee Shift Management').update(args).insert()
			esm.save()
   
   