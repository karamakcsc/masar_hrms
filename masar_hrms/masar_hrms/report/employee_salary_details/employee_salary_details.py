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
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "

	#SQL Query
	data = frappe.db.sql(f"""SELECT tss.name AS `Salary Slip No.`, tss.employee AS `Employee No.`,
									tss.employee_name AS `Employee Name`, tss.branch AS `Branch`, te.work_type AS `Work Type`, tss.company AS `Company`,
									tss.department AS `Department`, tss.designation AS `Designation`, te.date_of_joining AS `Date of Joining`,
									tss.leave_without_pay AS `Leave Without Pay`,
									tss.payment_days AS `Payment Days`,tssa.base AS `Basic Salary`,
									MAX(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Awards IN __ OUT'AND tsd.salary_component = 'Non Taxable Bonus' AND tsd.salary_component = 'End Service Awards' AND tsd.salary_component = 'Project Awards' AND tsd.salary_component = 'Award' AND tsd.salary_component = 'Bonus IN-OUT' THEN tsd.amount END) AS `Awards`,
									(SELECT SUM(IF(tsd.salary_component != 'Overtime Allowance' AND tsd.salary_component != 'Basic' AND tsd.salary_component != 'Awards IN __ OUT'AND tsd.salary_component != 'Non Taxable Bonus' AND tsd.salary_component != 'End Service Awards' AND tsd.salary_component != 'Project Awards' AND tsd.salary_component != 'Award' AND tsd.salary_component != 'Bonus IN-OUT', tsd.amount, 0))
									FROM `tabSalary Detail` tsd
									WHERE tsd.parent = tss.name AND tsd.parentfield = 'earnings') AS `Other Earnings`,
									tss.gross_pay AS `Total Earnings`,
									MAX(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
									MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
									MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,
									(SELECT SUM(IF(tsd.salary_component != 'Income Tax' AND tsd.salary_component != 'Social Security', tsd.amount, 0))
							FROM `tabSalary Detail` tsd
							WHERE tsd.parent = tss.name AND tsd.parentfield = 'deductions') AS `Other Deductions`, tss.total_deduction AS `Total Deductions`,
							tss.net_pay AS `Net Pay`, tss.posting_date
							FROM `tabSalary Slip` tss
							INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
							INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
							INNER JOIN `tabEmployee` te ON te.name = tss.employee
							INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
							WHERE tss.docstatus = 1 AND  tss_sub.name = tss.name
										And (tss.posting_date BETWEEN '{_from}' AND '{to}')
										{conditions}GROUP BY tss.name, tss.employee, tss.employee_name, tss.department,
										tss.designation, te.date_of_joining, tssa.base, tss.gross_pay, tss.payment_days,
										tss.total_deduction, tss.net_pay ;""")

	return data

def get_columns():
	return [
	   "Salary Slip No.: Link/Salary Slip:300",
	   "Employee No.:Link/Employee:200",
	   "Employee Name: Data:200",
	   "Branch: Data:200",
	   "Work Type: Data:200",
	   "Company: Data:300",
	   "Department: Data:200",
	   "Designation: Data:200",
	   "Date of Joining: Data:200 ",
	   #"Working Days: Data:200",
	   "Leave Without Pay: Data:200",
	   #"Absent Days: Data:200",
	   "Payment Days: Data:200",
	   "Basic Salary: Data:200",
	   "Overtime Allowance: Data:200",
	   "Awards: Data:200",
	   "Other Earnings: Data:200",
	   "Total Earnings: Data:200",
	   "Social Security: Data:200",
	   "Income Tax: Data:200",
	   "Loan: Data:200",
	   "Other Deductions: Data:200",
	   "Total Deductions: Data:200",
	   "Net Pay: Data:200"
	   #"Posting Date: Date/Posting Date:150"
	   # "Tax Group: Data:200",
	   # "Currency Code: Data:200"
	   #"Status:150"
	]
