# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
    if filters.get('school'):
        conditions += f" AND tee.custom_universitycollege = '{filters.get('school')}'"
    if filters.get('major'):
        conditions += f" AND tee.custom_major = '{filters.get('major')}'"
    if filters.get('is_engineer'):
        conditions += f" AND te.custom_is_engineer = '{filters.get('is_engineer')}'"
    if filters.get('level'):
        conditions += f" AND tee.custom_level_degree = '{filters.get('level')}'" 
    sql = frappe.db.sql(f"""
                        SELECT 
							te.name AS `Employee`, 
       						te.employee_name AS `Employee Name`, 
             				tee.custom_universitycollege AS `University/College`, 
							tee.custom_universitycollege_ar AS `University/College (AR)`,
                 			tee.custom_level_degree AS `Level/Degree`, 
                    		tee.custom_major AS `Major`, 
							tee.custom_major_ar AS `Major (AR)`,
       						tee.custom_year_of_graduation AS `Year of Graduation`,
							CASE 
       							WHEN te.custom_is_engineer = 1 Then 'Yes'
	   							ELSE 'No'
							END AS `Is Engineer`,
							tee.custom_remarks AS `Remarks`
						FROM tabEmployee te
						LEFT JOIN 
							`tabEmployee Education` tee ON tee.parent = te.name
						WHERE {conditions} AND tee.custom_is_qualification = 1
						ORDER BY
							te.name ASC;
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"University/College: Link:200",
		"University/College (AR): Data:200",
		"Level/Degree: Data:200",
		"Major: Link:200",
		"Major (AR): Data:200",
		"Year of Graduation: Data:200",
		"Is Engineer: Data:100",
		"Remarks: Data:300",
	]
