# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditons = " 1=1 "
    if filters.get('employee'):
        conditons += f" AND te.employee = '{filters.get('employee')}'"
    if filters.get('school'):
        conditons += f" AND tee.school_univ LIKE '%{filters.get('school')}%'"
    if filters.get('qualification'):
        conditons += f" AND tee.qualification LIKE '%{filters.get('qualification')}%'"
    if filters.get('major'):
        conditons += f" AND tee.maj_opt_subj LIKE '%{filters.get('major')}%'"
        
    sql = frappe.db.sql(f"""
                        SELECT 
							te.name, te.employee_name, tee.school_univ, tee.qualification, tee.`level`, 
       						tee.year_of_passing, tee.class_per, tee.maj_opt_subj
						FROM tabEmployee te
						LEFT JOIN 
							`tabEmployee Education` tee ON tee.parent = te.name
						WHERE {conditons}
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"School/University: Data:200",
		"Qulification: Data:200",
		"Level: Data:200",
		"Year of Passing: Int:200",
		"Class/Percentage: Data:200",
		"Major/Optional Subjects: Data:200",
	]
