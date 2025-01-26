# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    _from , to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
    
    if _from and to:
        conditions += f" AND tss.posting_date BETWEEN '{_from}' AND '{to}'"
    sql = frappe.db.sql(f"""
            SELECT
				te.name AS `Employee`, 
				te.first_name AS `First Name`,
				te.middle_name AS `Middle Name`,
				te.third_name AS `Third Name`,
				te.last_name AS `Last Name`,
				te.nationality AS `Nationality`,
				CASE
					WHEN te.nationality <> 'Jordan' THEN te.personal_no
					ELSE te.national_no
				END AS `National No`,
				te.social_security_number AS `Social Security No`,
				DAY(te.date_of_joining) AS `Date Of Joining Day`,
				MONTH(te.date_of_joining) AS `Date Of Joining Month`,
				YEAR(te.date_of_joining) AS `Date Of Joining Year`,
				te.social_security_salary AS `Social Security Salary`,
				te.gender AS `Gender`,
				te.custom_is_hazard AS `Is Hazard`
			FROM 
				tabEmployee te
			INNER JOIN
				`tabSalary Slip` tss ON te.name = tss.employee
			WHERE {conditions} AND te.status = 'Active' AND tss.docstatus = 1
			GROUP BY tss.name
        """)
    
    return sql

def get_columns():
    return[
		"Employee: Link/Employee:200",
		"First Name: Data:200",
		"Middle Name: Data:200",
		"Third Name: Data:200",
		"Last Name: Data:200",
		"Nationality: Data:200",
		"National No: Data:200",
		"Social Security No: Data:200",
		"Date Of Joining Day: Data:200",
		"Date Of Joining Month: Data:200",
		"Date Of Joining Year: Data:200",
		"Social Security Salary: Data:200",
		"Gender: Data:200",
		"Is Hazard: Check:200",
	]
