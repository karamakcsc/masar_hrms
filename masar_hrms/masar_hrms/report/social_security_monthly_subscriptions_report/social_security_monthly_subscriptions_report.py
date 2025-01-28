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
    if filters.get('year'):
        conditions += f" AND YEAR(tss.posting_date) = '{filters.get('year')}'"
    if filters.get('month'):
        conditions += f" AND MONTH(tss.posting_date) = '{filters.get('month')}'"
    if _from and to:
        conditions += f" AND tss.posting_date BETWEEN '{_from}' AND '{to}'"
    sql = frappe.db.sql(f"""
            SELECT
				te.name AS `Employee`, 
				te.employee_name AS `Employee Name`,
				te.nationality AS `Nationality`,
				CASE
					WHEN te.nationality <> 'Jordan' THEN te.personal_no
					ELSE te.national_no
				END AS `National No`,
				te.social_security_number AS `Social Security No`,
				te.date_of_birth AS `Date Of Birth`,
				te.social_security_salary AS `Social Security Salary`,
				te.custom_id_card_no AS `ID Card No`,
				tss.total_working_days AS `Working Days`,
				tss.payment_days AS `Payment Days`,
				te.custom_is_hazard AS `Is Hazard`
			FROM 
				tabEmployee te
			INNER JOIN
				`tabSalary Slip` tss ON te.name = tss.employee
			WHERE {conditions} AND te.status = 'Active' AND tss.docstatus = 1 AND tss.payment_days >= 16
			GROUP BY tss.name
        """)
    
    return sql

def get_columns():
    return[
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Nationality: Data:200",
		"National No/Personal No: Data:200",
		"Social Security No: Data:200",
		"Date Of Birth: Data:200",
		"Social Security Salary: Data:200",
		"ID Card No: Data:200",
		"Working Days: Data:200",
		"Payment Days: Data:200",
		"Is Hazard: Check:200",
	]
