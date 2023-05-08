# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	_from, to = filters.get('from'), filters.get('to') #date range
	#Conditions
	conditions = " AND 1=1 "
	if(filters.get('bank')):conditions += f" AND te.bank = '{filters.get('bank')}' "
	if(filters.get('bank_branch')):conditions += f" AND te.bank_branch = '{filters.get('bank_branch')}' "
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	#if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "

	#SQL Query
	data = frappe.db.sql(f"""SELECT tb.swift_number AS `SWIFT Number`, te.name AS `Employee Number`, te.full_name_ar AS `Employee Name`, te.department AS `Department`,
									MONTH(tss.posting_date) AS `Month`, IF(te.national_no IS NULL, te.personal_no, IF(te.national_no = '', '', te.national_no)) AS `National Number`, 
									te.iban AS `IBAN`, te.bank AS `Bank Name`, te.bank_branch AS `Bank Branch`,
									 te.bank_ac_no AS `Account Number`, tss.gross_pay AS `Transfer Amount`
							FROM `tabSalary Slip` tss
							INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
							INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
							INNER JOIN `tabEmployee` te ON te.name = tss.employee
							INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
							INNER JOIN `tabBank` tb on te.bank = tb.name 
							WHERE tss.docstatus = 1 AND tssa.docstatus = 1 AND tss_sub.name = tss.name
										And (tss.posting_date BETWEEN '{_from}' AND '{to}')
										{conditions} GROUP BY te.name, te.full_name_ar, tss.posting_date, 
										tss.gross_pay, te.iban, te.bank, te.bank_branch, te.bank_ac_no, tb.name ,tb.swift_number ;""")

	return data

def get_columns():
	return [
		"SWIFT Number: Data:250",
	   "Employee Number: Link/Employee:200",
	   "Employee Name: Data:200",
	   "Department: Data:250",
	   "Month: Data:150",
	   "National Number:Data:200",
	   "IBAN: Data:200",
	   "Bank Name: Data:200",
	   "Bank Branche: Data:200",
	   "Account Number: Data:300",
	   "Transfer Amount: Currency:200"
	]