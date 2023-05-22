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
	if(filters.get('ss_no')):conditions += f" AND tss.name LIKE '%{filters.get('ss_no')}' "
	# if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND employee LIKE '%{filters.get('emp_name')}' "
	# if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	# if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	# if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND department LIKE '%{filters.get('dep')}' "

	#SQL Query
	data = frappe.db.sql(f"""select name, employee, employee_name, department, base, from_date, modification_date, amended_from 
								from `tabSalary Structure Assignment` tssa 
								where change_basic_amount = 1
										And (from_date BETWEEN '{_from}' AND '{to}')
										{conditions} ;""")

	return data

def get_columns():
	return [
	   "Salary Structure Assignment: Link/Salary Structure Assignment:300",
	   "Employee No.:Link/Employee:200",
	   "Employee Name: Data:200",
	   #"Branch: Data:200",
	   #"Work Type: Data:200",
	   #"Company: Data:300",
	   "Department: Data:200",
	   "Basic Salary: Data: Currency:200",
	   "From Date: Data:200 ",
	   #"Working Days: Data:200",
	   "Modification Date: Data:200",
	   #"Absent Days: Data:200",
	   "Last Salary Structure Assignment: Link/Salary Structure Assignment:300"
	#    "Basic Salary: Currency:200",
	#    "Overtime Allowance: Currency:200",
	#    "Awards: Currency:200",
	#    "Other Earnings: Currency:200",
	#    "Total Earnings: Currency:200",
	#    "Social Security: Currency:200",
	#    "Income Tax: Currency:200",
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
