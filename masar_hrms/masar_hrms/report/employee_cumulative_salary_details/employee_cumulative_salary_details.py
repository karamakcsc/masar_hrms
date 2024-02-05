# Copyright (c) 2024, KCSC and contributors
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
	data = frappe.db.sql(f""" With p AS
							(
							Select tge.posting_date ,tge.party ,tge.account, SUM(tge.debit_in_account_currency)  AS pay_amount
							From `tabGL Entry` tge 
							Where tge.voucher_type IN ('Journal Entry', 'Payment Entry') AND tge.is_cancelled = 0 AND tge.docstatus = 1
							Group By tge.posting_date ,tge.party ,tge.account
							)
							SELECT
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
								tss.net_pay AS `Net Pay Salary`,
								pay_amount AS `Net Pay Amount`,
        						tss.net_pay - pay_amount AS `Balance Amount`,
					  			(MAX(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) * (tc.company_share_rate) / 100) / (tc.employee_share_rate / 100) AS `Social Security for Company Contribution`,
					 			tss.posting_date,
         						DATE_FORMAT(tss.posting_date, '%m') AS `Month`,
         						te.old_ref AS `Old Reference`
								
							FROM
								`tabSalary Slip` tss
							INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
							INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
							INNER JOIN `tabEmployee` te ON te.name = tss.employee
							INNER JOIN `tabCompany` tc ON tss.company = tc.name
							INNER JOIN `tabPayroll Entry` tpe ON tpe.name = tss.payroll_entry AND tpe.docstatus = 1 AND tpe.posting_date = tss.posting_date
							INNER JOIN p  ON p.posting_date = tss.posting_date AND p.party = tss.employee AND p.account = tssa.payroll_payable_account 
							WHERE
								tss.docstatus = 1 AND tssa.docstatus = 1  AND tpe.docstatus = 1 AND (tss.posting_date BETWEEN '{_from}' AND '{to}') {conditions}
							GROUP BY
								tss.name, tss.employee, tss.employee_name, tss.branch, te.work_type, tss.company, tss.department, tss.designation, te.date_of_joining,
								tssa.base, tss.gross_pay, tss.leave_without_pay, tss.payment_days, te.old_ref, tss.total_deduction, tss.net_pay, tss.posting_date
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
	   "Other Deductions: Currency:150",
	   "Total Deductions: Currency:150",
	   "Net Pay Salary: Currency:150",
	   "Net Pay Amount: Currency:200",
	   "Balance Amount: Currency:200",
	   "Social Security for Company Contribution: Currency:300",
       "Posting Date:150",
       "Month:150",
	   "Old Reference: Data:150"
	#    "Posting Date:150"
	]
# to add loan in the report siam
# MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,