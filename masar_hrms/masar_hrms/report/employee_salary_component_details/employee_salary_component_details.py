# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	conditions = " AND 1=1 "
	if(filters.get('ss_no')):conditions += f" AND te.name LIKE '%{filters.get('ss_no')}' "
	if(filters.get('company')):conditions += f" AND te.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND te.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND te.designation LIKE '%{filters.get('des')}' "
	if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND te.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND te.department LIKE '%{filters.get('dep')}' "
	_from, to = filters.get('from'), filters.get('to')
	if _from and to:
		conditions += f" AND tss.start_date BETWEEN '{_from}' AND '{to}' "

	components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])
	earnings = [c.name for c in components if c.type == "Earning"]
	deductions = [c.name for c in components if c.type == "Deduction"]

	ordered_components = earnings + deductions

	salary_fields = ""
	for comp in ordered_components:
		salary_fields += f"MAX(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"

	query = f"""
		SELECT te.name AS `Employee No.`, te.employee_name AS `Employee Name`,
			te.date_of_joining AS `Date of Joining`, te.work_type AS `Work Type`,
			tss.company AS `Company`, te.branch AS `Branch`, te.department AS `Department`,
			te.designation AS `Designation`,
			{salary_fields}
			te.social_security_amount AS `Social Security`
		FROM `tabSalary Slip` tss
		INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
		INNER JOIN `tabSalary Detail` tsd ON tsd.parent = tss.name
		INNER JOIN `tabSalary Component` tsc ON tsd.salary_component = tsc.name
		INNER JOIN `tabEmployee` te ON tss.employee = te.name
		INNER JOIN `tabEmployee Social Security Salary` tesss ON te.name = tesss.employee
		WHERE tss.docstatus = 1
		{conditions}
		GROUP BY tss.name, te.employee, te.social_security_amount
	"""

	data = frappe.db.sql(query)
	return data

def get_columns():
	columns = [
		"Employee No.:Link/Employee:200",
		"Employee Name: Data:200",
		"Date of Joining: Data:200",
		"Work Type: Data:200",
		"Company: Data:300",
		"Branch: Data:200",
		"Department: Data:200",
		"Designation: Data:200",
	]

	components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])

	earnings = [c.name for c in components if c.type == "Earning"]
	deductions = [c.name for c in components if c.type == "Deduction"]

	for comp in earnings:
		columns.append(f"{comp}:Data:200")

	for comp in deductions:
		columns.append(f"{comp}:Data:200")

	return columns
