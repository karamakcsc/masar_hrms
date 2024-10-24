# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND tss.employee = '{filters.get('employee')}'"
    if filters.get('salary_component'):
        conditions += f" AND tsd.salary_component = '{filters.get('salary_component')}'"
    if filters.get('department'):
        conditions += f" AND tss.department = '{filters.get('department')}'"
        
    sql = frappe.db.sql(f"""
                        SELECT tss.employee, tss.employee_name, tss.department, tss.start_date, tss.end_date, tsd.salary_component, tsd.amount 
						FROM `tabSalary Slip` tss
						INNER JOIN `tabSalary Detail` tsd ON tsd.parent = tss.name AND tsd.parentfield = 'deductions'
						WHERE {conditions}
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Department: Link/Department:200",
		"Start Date: Date:200",
		"End Date: Date:200",
		"Salary Component: Link/Salary Component:200",
		"Amount: Currency:200"
	]
