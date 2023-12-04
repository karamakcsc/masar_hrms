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
	data = frappe.db.sql(f"""SELECT
								tss.name AS `Salary Slip No.`,
								tss.employee AS `Employee No.`,
								tss.employee_name AS `Employee Name`,
								tss.branch AS `Branch`,
								te.work_type AS `Work Type`,
								tss.company AS `Company`,
								tss.department AS `Department`,
								tss.designation AS `Designation`,
								te.date_of_joining AS `Date of Joining`,
					  			tssa.base AS 'Basic Salary',
								tss.gross_pay AS `Reserved Salary`,
								tss.leave_without_pay AS `Leave Without Pay`,
								tss.payment_days AS `Payment Days`,
								MAX(CASE WHEN tsd.salary_component = 'Basic' THEN tsd.amount END) AS `Reserved Basic Salary`,
								MAX(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
								MAX(CASE WHEN tsd.salary_component IN ('Awards IN __ OUT', 'Non Taxable Bonus', 'End Service Awards', 'Project Awards', 'Award', 'Bonus IN-OUT') THEN tsd.amount END) AS `Awards`,
								(SELECT SUM(IF(tsd.salary_component NOT IN ('Overtime Allowance', 'Basic', 'Awards IN __ OUT', 'Non Taxable Bonus', 'End Service Awards', 'Project Awards', 'Award', 'Bonus IN-OUT'), tsd.amount, 0))
								FROM `tabSalary Detail` tsd
								WHERE tsd.parent = tss.name AND tsd.parentfield = 'earnings') AS `Other Earnings`,
								tss.gross_pay AS `Total Earnings`,
								MAX(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
								MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
								(SELECT SUM(IF(tsd.salary_component NOT IN ('Income Tax', 'Social Security'), tsd.amount, 0))
								FROM `tabSalary Detail` tsd
								WHERE tsd.parent = tss.name AND tsd.parentfield = 'deductions') AS `Other Deductions`,
								tss.total_deduction AS `Total Deductions`,
								tss.net_pay AS `Net Pay`,
								te.old_ref AS `Old Reference`,
								tss.posting_date
							FROM
								`tabSalary Slip` tss
							INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
							INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
							INNER JOIN `tabEmployee` te ON te.name = tss.employee
							INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
							WHERE
								tss.docstatus = 1 AND tssa.docstatus = 1 AND tss_sub.name = tss.name
								And (tss.posting_date BETWEEN '{_from}' AND '{to}') {conditions}
							GROUP BY
								tss.name, tss.net_pay, tssa.base
								;
							""")

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
	   "Date of Joining: Data:150 ",
	   "Basic Salary: Currency:150",
	   "Reserved Salary: Currency:150",
	   "Leave Without Pay: Data:150",
	   #"Absent Days: Data:200",
	   "Payment Days: Data:150",
	   "Reserved Basic Salary: Currency:150",
	   "Overtime Allowance: Currency:150",
	   "Awards: Currency:150",
	   "Other Earnings: Currency:150",
	   "Total Earnings: Currency:150",
	   "Social Security: Currency:150",
	   "Income Tax: Currency:150",
	   #"Loan: Currency:200",
	   "Other Deductions: Currency:150",
	   "Total Deductions: Currency:150",
	   "Net Pay: Currency:150",
	   "Old Reference: Data:150"
	   #"Posting Date: Date/Posting Date:150"
	   # "Tax Group: Data:200",
	   # "Currency Code: Data:200"
	   #"Status:150"
	]
# to add loan in the report siam
# MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,