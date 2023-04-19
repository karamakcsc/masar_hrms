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
	if(filters.get('ss_no')):conditions += f" AND te.social_security_number = '{filters.get('ss_no')}' "
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "

	#SQL Query
	data = frappe.db.sql(f"""SELECT te.social_security_number AS `Social Security Number`, te.tax_type AS `TAX TYPE`,
									te.full_name_ar AS `Full Name Arabic`, MONTH(tss.posting_date) AS `Month`,
									tss.gross_pay AS `Total Salary`,
									MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`
							FROM `tabSalary Slip` tss
							INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
							INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
							INNER JOIN `tabEmployee` te ON te.name = tss.employee
							INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
							WHERE tss.docstatus = 1 AND tssa.docstatus = 1 AND tss_sub.name = tss.name
										And (tss.posting_date BETWEEN '{_from}' AND '{to}')
										{conditions} GROUP BY te.social_security_number, te.tax_type, te.full_name_ar, tss.posting_date, 
										tss.gross_pay, te.old_ref ;""")

	return data

def get_columns():
	return [
	   "Social Security Number: Data:200",
	   "TAX TYPE: Data:200",
	   "Full Name Arabic: Data:250",
	   "Month: Data:150",
	   "Total Salary: Currency:200",
	   "Income Tax: Currency:200"
	   
	   
	   
	   
	#    "Employee No.:Link/Employee:200",
	#    "Employee Name: Data:200",
	#    "Branch: Data:200",
	#    "Work Type: Data:200",
	#    "Company: Data:300",
	#    "Department: Data:200",
	#    "Designation: Data:200",
	#    "Date of Joining: Data:200 ",
	#    #"Working Days: Data:200",
	#    "Leave Without Pay: Data:200",
	#    #"Absent Days: Data:200",
	#    "Payment Days: Data:200",
	#    "Basic Salary: Currency:200",
	#    "Overtime Allowance: Currency:200",
	#    "Awards: Currency:200",
	#    "Other Earnings: Currency:200",
	#    "Social Security: Currency:200",
	   
	#    "Loan: Currency:200",
	#    "Other Deductions: Currency:200",
	#    "Total Deductions: Currency:200",
	#    "Net Pay: Currency:200",
	#    "Old Reference: Data:200"
	   #"Posting Date: Date/Posting Date:150"
	   # "Tax Group: Data:200",
	   # "Currency Code: Data:200"
	   #"Status:150"
	]
