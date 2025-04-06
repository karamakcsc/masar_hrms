# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	_from, to = filters.get('from'), filters.get('to') #date range
	#Conditions
	conditions = " 1=1 "
	if(filters.get('department')):conditions += f" AND tss.department LIKE '%{filters.get('department')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(_from and to):conditions += f" AND (tss.start_date BETWEEN '{_from}' AND '{to}')"
	

	#SQL Query
	data = frappe.db.sql(f"""
		WITH base_amount AS (
			SELECT 
				tss.employee AS `e_id`,
				tss.employee_name AS `e_name`,
				tss.department AS `e_dep`,
				SUM(tss.gross_pay) AS `gross_pay`,
				SUM(tss.payment_days) AS `payment_days`,
				SUM(tss.net_pay) AS `net_pay`,
				te.nationality AS `nationality`,
				te.marital_status AS `martial_status`
			FROM `tabSalary Slip` tss
			INNER JOIN tabEmployee te ON te.name = tss.employee
			WHERE {conditions} AND tss.docstatus = 1 
			GROUP BY tss.employee
		)
			SELECT 
				ba.e_id AS `Employee ID`,
				ba.e_name AS `Employee Name`,
				ba.e_dep AS `Depatrment`,
				SUM(CASE WHEN tsd.salary_component = 'Basic' THEN tsd.amount END) AS `Basic Salary`,
				SUM(CASE WHEN tsd.parentfield = 'earnings' AND tsd.salary_component NOT IN ('Basic') THEN tsd.amount END) AS `Total Allowances`,
				SUM(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Total Overtime`,
				SUM(CASE WHEN tsd.parentfield = 'earnings' AND tsd.salary_component NOT IN ('Basic', 'Overtime Allowance') THEN tsd.amount END) AS `Other Earnings`,
				ba.gross_pay AS `Total Earnings`,
				SUM(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
				SUM(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
				SUM(CASE WHEN tsd.salary_component = 'Loan' THEN tsd.amount END) AS `Loan`,
				SUM(CASE WHEN tsd.parentfield = 'deductions' AND tsd.salary_component NOT IN ('Social Security', 'Income Tax', 'Loan') THEN tsd.amount END) AS `Other Deductions`,
				ba.payment_days AS `Payment Days`,
				ba.net_pay AS `Net Pay`,
				ba.nationality AS `Nationality`,
				ba.martial_status AS `Marital Status`
			FROM base_amount ba
			LEFT JOIN `tabSalary Slip` tss ON tss.employee = ba.e_id
				AND tss.employee = ba.e_id
				AND tss.docstatus = 1
			LEFT JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
			WHERE {conditions}
			GROUP BY ba.e_id
			ORDER BY ba.e_id ASC
			;
		""")

	return data

def get_columns():
	return [
	   	"Employee ID:Link/Employee:200",
	   	"Employee Name: Data:200",
		"Department:Link/Department:200",
	   	"Basic Salary: Currency:150",
		"Total Allowances: Currency:150",
		"Total Overtime: Currency:150",
		"Other Earnings: Currency:150",
		"Total Earnings: Currency:150",
		"Social Security: Currency:150",
		"Income Tax: Currency:150",
		"Loan: Currency:150",
		"Other Deduction: Currency:150",
	   	"Payment Days: Data:150",
		"Net Pay: Currency:150",
		"Nationality: Data:150",
		"Martial Status: Data:150",
	]