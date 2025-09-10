# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	_from, to = filters.get('from'), filters.get('to')
	conditions = " AND 1=1 "
	if(filters.get('bank')):conditions += f" AND te.bank = '{filters.get('bank')}' "
	if(filters.get('bank_branch')):conditions += f" AND te.bank_branch = '{filters.get('bank_branch')}' "
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "
	if(filters.get('work_type')):conditions += f" AND te.work_type = '{filters.get('work_type')}' "
	if filters.get('with_temp'):
		if filters.get('with_temp') == 'HOUSING BANK FOR TRADE AND FINANCE':
			select = """
				te.name AS `ID`,
				IF(te.national_no IS NULL, te.personal_no, IF(te.national_no = '', '', te.national_no)) AS `National Number`, 
				tb.swift_number as `Swift Code`,
				te.bank AS `Bank`,
				te.iban AS `IBAN`,
				te.employee_name as `Name`,
				tss.net_pay AS `Amount`
			"""
		elif filters.get('with_temp') == 'Ahli Bank':
			select = """
				te.name AS `ID`,
				tb.swift_number as `Swift Code`,
				te.iban AS `IBAN`,
				te.employee_name as `Employee Name`,
				tss.net_pay AS `Salary Amount`
			"""
		elif filters.get('with_temp') == 'Capital Bank':
			select = """
				tb.swift_number as `Swift Code`,
				te.employee_name as `Employee Name`,
				te.iban AS `IBAN`,
				te.bank AS `Bank`,
				tss.net_pay AS `Amount`, 
				'202' as `Payment purpose code`
			"""
	else:
		select = """
			tb.swift_number AS `SWIFT Number`, 
			te.name AS `Employee Number`, 
			te.employee_name AS `Employee Name`,
			te.full_name_ar AS `Employee Name AR`, 
			te.department AS `Department`,
			MONTH(tss.posting_date) AS `Month`, 
			IF(te.national_no IS NULL, te.personal_no, IF(te.national_no = '', '', te.national_no)) AS `National Number`, 
			te.iban AS `IBAN`, 
			te.bank AS `Bank Name`, 
			te.bank_branch AS `Bank Branch`,
			te.bank_ac_no AS `Account Number`, 
			tss.net_pay AS `Transfer Amount`
		"""
	data = frappe.db.sql(f"""SELECT 
		{select}
		FROM `tabSalary Slip` tss
		INNER JOIN `tabEmployee` te ON te.name = tss.employee
		LEFT JOIN `tabBank` tb on te.bank = tb.name 
		WHERE 
			tss.docstatus = 1 
			AND te.salary_mode = 'Bank'
			AND (tss.posting_date BETWEEN '{_from}' AND '{to}')
			{conditions} 
		GROUP BY te.name;""")

	return data

def get_columns(filters):
	if filters.get('with_temp'):
		if filters.get('with_temp') == 'HOUSING BANK FOR TRADE AND FINANCE':
			return [
				"ID: Data:200",
				"National Number: Data:200",
				"Swift Code: Data:200",
				"Bank: Data:200",
				"IBAN: Data:200",
				"Name: Data:200",
				"Amount: Currency:200"
			]
		elif filters.get('with_temp') == 'Ahli Bank':
			return [
				"ID: Data:200",
				"Swift Code: Data:200",
				"IBAN: Data:200",
				"Employee Name: Data:200",
				"Salary Amount: Currency:200"
			]
		elif filters.get('with_temp') == 'Capital Bank':
			return [
				"Swift Code: Data:200",
				"Employee Name: Data:200",
				"IBAN: Data:200",
				"Bank: Data:200",
				"Amount: Currency:200",
				"Payment purpose code: Data:200"
			]
	return [
		"SWIFT Number: Data:250",
		"Employee Number: Link/Employee:150",
		"Employee Name: Data:250",
		"Employee Name AR: Data:200",
		"Department: Data:250",
		"Month: Data:150",
		"National Number: Data:200",
		"IBAN: Data:200",
		"Bank Name: Data:200",
		"Bank Branch: Data:200",
		"Account Number: Data:300",
		"Transfer Amount: Currency:200"
	]