# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
    if filters.get('department'):
        conditions += f" AND teiwh.employee = '{filters.get('department')}'"
    if filters.get('designation'):
        conditions += f" AND teiwh.designation = '{filters.get('designation')}'"
        
    sql = frappe.db.sql(f"""
                        SELECT 
							te.name, te.employee_name, tee.qualification, teewh.company_name,
							teewh.designation, teewh.salary, teewh.total_experience, teiwh.branch, teiwh.department, 
							teiwh.designation, teiwh.from_date, teiwh.to_date 
						FROM tabEmployee te
						LEFT JOIN 
							`tabEmployee Education` tee ON tee.parent = te.name
						LEFT JOIN 
							`tabEmployee External Work History` teewh ON teewh.parent = te.name
						LEFT JOIN 
							`tabEmployee Internal Work History` teiwh ON teiwh.parent = te.name
						WHERE {conditions}
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Qualification: Data:200",
		"Company Name: Data:200",
		"Designation: Data/Designation:200",
		"Salary: Currency:200",
		"Total Experience: Float:200",
		"Branch: Link/Branch:200",
		"Department: Link/Department:200",
		"Designation: Link/Designation:200",
		"From Date: Date:200",
		"To Date: Date:200",
	]
