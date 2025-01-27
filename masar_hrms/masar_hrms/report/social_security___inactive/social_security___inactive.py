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
				te.name AS `Employee Number`,
				te.employee_name AS `Employee Name`,
				te.social_security_number AS `Social Security Number`,
				YEAR(
					CASE 
						WHEN te.status = 'Left' THEN te.relieving_date
						ELSE tss.posting_date
					END
				) AS `Date Of Inactive Year`,
				MONTH(
					CASE 
						WHEN te.status = 'Left' THEN te.relieving_date
						ELSE tss.posting_date
					END
				) AS `Date Of Inactive Month`,
				DAY(
					CASE 
						WHEN te.status = 'Left' THEN te.relieving_date
						ELSE tss.posting_date
					END
				) AS `Date Of Inactive Day`,
				CASE
					WHEN te.status = 'Left' THEN "Resigned"
					ELSE "Inactive"
				END AS `Reason For Inactive`
			FROM tabEmployee te
			INNER JOIN `tabSalary Slip` tss ON tss.employee = te.name 
			INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
			WHERE {conditions} AND tss.docstatus = 1 AND tss.payment_days < 16
			GROUP BY tss.name;

        """)
    
    return sql

def get_columns():
    return[
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Social Security No: Data:200",
		"Date Of Inactive Year: Data:200",
		"Date Of Inactive Month: Data:200",
		"Date Of Inactive Day: Data:200",
		"Reason: Data:200",
	]
