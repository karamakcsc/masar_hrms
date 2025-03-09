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
				te.name AS `Employee Number`,
				te.employee_name AS `Employee Name`,
				CASE
					WHEN te.nationality <> 'Jordan' THEN te.personal_no
					ELSE te.national_no
				END AS `National No`,
				te.custom_id_card_no AS `ID Card No`,
				te.date_of_birth AS `Date Of Birth`,
				te.date_of_joining AS `Date Of Joining`,
				te.social_security_number AS `Social Security Number`,
				CASE 
						WHEN te.status = 'Left' THEN te.relieving_date
						ELSE tss.posting_date
					END AS `Date Of Inactive`,
				CASE
					WHEN te.status = 'Left' THEN "Resigned"
					ELSE "Leave Without Pay"
				END AS `Reason For Inactive`,
				tss.total_working_days AS `Working Days`,
				tss.payment_days AS `Payment Days`,
				te.designation AS `Designation`,
				CASE
					WHEN te.custom_is_hazard = 1 THEN td.hazard_code
					ELSE ""
				END AS `Hazard Code`
			FROM tabEmployee te
			INNER JOIN `tabSalary Slip` tss ON tss.employee = te.name 
			INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
			INNER JOIN `tabDesignation` td ON te.designation = td.name
			WHERE 
   				{conditions} 
   				AND tss.docstatus = 1 
       			AND tss.payment_days < 16 
          		AND (
                (te.status = 'Left' AND te.relieving_date IS NOT NULL)
                OR (MONTH(te.date_of_joining) <> MONTH(tss.posting_date))
				)
			GROUP BY tss.name;

        """)
    
    return sql

def get_columns():
    return[
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"National No/Personal No: Data:200",
		"ID Card No: Data:200",
		"Date of Birth: Date:200",
		"Date Of Joining: Data:200",
		"Social Security No: Data:200",
		"Date Of Inactive: Date:200",
		"Reason For Inactive: Data:200",
		"Working Days: Data:200",
		"Payment Days: Data:200",
		"Designation: Data:200",
		"Hazard Code: Data:200",
	]
