# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
#
# class OvertimeApplication(Document):
# 	pass

import frappe
# from __future__ import unicode_literals
import erpnext, json
from frappe import _, scrub, ValidationError
from frappe.utils import flt, comma_or, nowdate, getdate
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe.model.document import Document
from frappe.model.document import Document
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift

class OvertimeApplication(Document):
	def __init__(self, *args, **kwargs):
		super(OvertimeApplication, self).__init__(*args, **kwargs)

	def validate(self):
		calculate_overtime_amount(self)
		# self.reload()
	def on_submit(self):
		for employee in self.overtime_employees:
			if frappe.get_doc("Employee", employee.employee).is_overtime_applicable:
				defAddAdditionalSalary(self, employee.employee, employee.salary_component, employee.amount, self.posting_date)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_employee_qry(doctype, txt, searchfield, start, page_len, filters):
	vr_dep = filters.get('department')
	return frappe.db.sql("""
		Select name,employee,employee_name,department, default_shift
		From `tabEmployee` te
		Where department = '%s' """%(vr_dep) ,as_dict=True)



@frappe.whitelist()
def insert_selected_employee(selected_employees):
	selected_employees = json.loads(selected_employees)
	rows = []
	for employee in selected_employees:
		employee_doc = frappe.get_doc("Employee", employee)
		rows.append({
			'name': employee
		})
	return rows


@frappe.whitelist()
def calculate_overtime_amount(self):
	posting_date = datetime.datetime.strptime(self.posting_date, '%Y-%m-%d')
	for employee in self.overtime_employees:
		if frappe.get_doc("Employee", employee.employee).is_overtime_applicable:
			total_overtime_hours=get_total_overtime_hours_for_employee(employee.employee,posting_date.month)[0].hours
			taken_overtime_hours=0
			if total_overtime_hours != None:
				taken_overtime_hours=int(total_overtime_hours)
			if taken_overtime_hours+employee.overtime_hours>frappe.get_doc("Employee", employee.employee).overtime_ceiling:
				frappe.throw(employee.employee + " " + employee.employee_name + " don't have enough remaining overtime hours")
			overtime_type_hour_rate=frappe.get_doc("Overtime Type", employee.overtime_type).rate
			result=get_employee_shift(employee.employee, posting_date, consider_default_shift=True)
			plan_hours=0
			if result:
				if result.start_datetime.minute>result.end_datetime.minute:
					plan_hours=(result.end_datetime.hour-result.start_datetime.hour-1)+(60-result.start_datetime.minute+result.end_datetime.minute)/60.0
				else:
					plan_hours=(result.end_datetime.hour-result.start_datetime.hour)+(result.end_datetime.minute-result.start_datetime.minute)/60.0
			elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
				plan_hours=frappe.db.get_single_value("HR Settings", "standard_working_hours")
			else:
				frappe.throw("You have to assign a shift for the employee or assign standar working hours in HR Settings")

			#month_working_hours=flt(plan_hours)*30
			month_working_hours=8*30
			
			entry = {
				"employee": employee.employee,
				"posting_date": posting_date
			}
			sl = frappe.new_doc('Salary Slip')
			sl.update(entry)
			sl.get_emp_and_working_day_details()
			overtime_components_amount=0
			for d in sl.get('earnings'):
				doc = frappe.get_doc('Salary Component', d.get('salary_component'))
				if doc.is_overtime_applicable:
					overtime_components_amount+=int(d.amount)
			for d in sl.get('deductions'):
				doc = frappe.get_doc('Salary Component', d.get('salary_component'))
				if doc.is_overtime_applicable:
					overtime_components_amount-=int(d.amount)
			overtime_components_amount=max(0, overtime_components_amount)
			# frappe.msgprint(str(overtime_components_amount))
			hour_rate=flt(overtime_components_amount)/month_working_hours
			employee.rate=round(hour_rate*flt(overtime_type_hour_rate),3)

			# self.reload()
			# frappe.throw("alaa")
			if employee.overtime_hours==0:
				frappe.throw("Please fill overtime hours field")
			employee.amount=round(flt(employee.rate)*int(employee.overtime_hours),3)
			# self.reload()
			# frappe.msgprint(str(employee.amount))
		# frappe.msgprint(str(sl.net_pay))

@frappe.whitelist()
def defAddAdditionalSalary(self, employee_no,salary_component,amount,payroll_date):
	# frappe.msgprint(employee_no)
	# frappe.msgprint(str(salary_component))
	# frappe.msgprint(str(amount))
	# frappe.msgprint(str(payroll_date))
	entry = {
		"employee": employee_no,
		"salary_component": salary_component,
		"company": self.company,
		"currency": frappe.get_doc("Company", self.company).default_currency,
		"amount": flt(amount),
		"payroll_date": payroll_date,

	}
	(frappe.new_doc("Additional Salary")
		.update(entry)
		.insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
	frappe.db.commit()


@frappe.whitelist()
def get_total_overtime_hours_for_employee(employee, month):
	return frappe.db.sql(f"""
		Select sum(toe.overtime_hours) as hours
		From `tabOvertime Employee` toe
		inner join `tabOvertime Application` toa on toe.parent = toa.name
		Where toa.docstatus=1 and toe.employee = '{employee}' and month(toa.posting_date) ='{month}' """,as_dict=True)
