# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = ""
    _from, to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
    if _from and to:
        conditions += f" AND te.date_of_joining BETWEEN '{_from}' AND '{to}'"
    if filters.get('department'):
        conditions += f" AND te.department = '{filters.get('department')}'"
    if filters.get('designation'):
        conditions += f" AND te.designation = '{filters.get('designation')}'"
        
    sql = frappe.db.sql(f"""
                        SELECT 
                            te.employee, 
                            te.employee_name, 
                            te.department, 
                            te.designation, 
                            te.date_of_joining,
                            CONCAT(
								TIMESTAMPDIFF(YEAR, te.date_of_joining, CURDATE()), ' years and ',
								TIMESTAMPDIFF(MONTH, te.date_of_joining, CURDATE()) % 12, ' months'
							) AS `Years at Company`
						FROM tabEmployee te 
						WHERE te.status = 'Active' {conditions}
                        ORDER BY te.employee ASC;
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
        "Department: Link/Department:200",
        "Designation: Link/Designation:200",
		"Date of Joining: Date:200",
        "Years at Company: Data:200",
	]
