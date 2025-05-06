# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = ""
    _from, to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND tss.employee = '{filters.get('employee')}'"
    if filters.get('department'):
        conditions += f" AND tss.department = '{filters.get('department')}'"
    if _from and to:
        conditions += f" AND tas.payroll_date BETWEEN '{_from}' AND '{to}'"
        
    sql = frappe.db.sql(f"""
                        SELECT 
                            tas.employee, 
                            tas.employee_name, 
                            tas.department, 
                            te.designation,
                            CASE
                                WHEN tas.salary_component IN ('Overtime Allowance MID', 'Overtime Allowance') 
                                THEN tas.amount
                            END AS `Overtime Amount`, 
                            tas.payroll_date 
						FROM `tabAdditional Salary` tas
                        INNER JOIN tabEmployee te ON tas.employee = te.name
						WHERE tas.salary_component = 'Overtime Allowance' {conditions}
                        ORDER BY tas.employee ASC;
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Department: Link/Department:200",
        "Designation: Data:200",
		"Overtime Amount: Float:200",
		"Payroll Date: Date:200"
	]
