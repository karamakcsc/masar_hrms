# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	# _from, to = filters.get('from'), filters.get('to') #date range
	#Conditions
	conditions = " AND 1=1 "
	if(filters.get('ss_no')):conditions += f" AND te.name LIKE '%{filters.get('ss_no')}' "
	if(filters.get('company')):conditions += f" AND te.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND te.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND te.designation LIKE '%{filters.get('des')}' "
	if(filters.get('work_type')):conditions += f" AND te.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND te.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND te.department LIKE '%{filters.get('dep')}' "

	#SQL Query
	# data = frappe.db.sql(f"""SELECT tss.employee AS `Employee No.`,
	# 								tss.employee_name AS `Employee Name`, tss.branch AS `Branch`, te.work_type AS `Work Type`, tss.company AS `Company`,
	# 								tss.department AS `Department`, tss.designation AS `Designation`, te.date_of_joining AS `Date of Joining`,
	# 								tssa.base AS `Basic Salary`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Transportation' THEN tsd.amount END) AS `Transportation`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Expatriate Allowance' THEN tsd.amount END) AS `Expatriate Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Mobile Allowance' THEN tsd.amount END) AS `Mobile Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Field Allowance' THEN tsd.amount END) AS `Field Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Housing' THEN tsd.amount END) AS `Housing`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Work days allowance' THEN tsd.amount END) AS `Work Days Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Project Awards' THEN tsd.amount END) AS `Project Awards`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Fixed Allowance' THEN tsd.amount END) AS `Fixed Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Fuel Allowance' THEN tsd.amount END) AS `Fuel Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Fund Allowance' THEN tsd.amount END) AS `Fund Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Master Degree Allowance' THEN tsd.amount END) AS `Master Degree Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Board Allowance' THEN tsd.amount END) AS `Board Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Children Education Allowance' THEN tsd.amount END) AS `Children Education Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'End Service Awards' THEN tsd.amount END) AS `End Service Awards`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Award' THEN tsd.amount END) AS `Award`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Arrear' THEN tsd.amount END) AS `Arrear`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Leave Encashment' THEN tsd.amount END) AS `Leave Encashment`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Medical Treatment Allowance' THEN tsd.amount END) AS `Medical Treatment Allowance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Non Taxable Bonus' THEN tsd.amount END) AS `Non Taxable Bonus`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Notice Period' THEN tsd.amount END) AS `Notice Period`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Refunds' THEN tsd.amount END) AS `Refunds`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Salaries Differences - Earning' THEN tsd.amount END) AS `Salaries Differences-Earning`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Social Security Difference' THEN tsd.amount END) AS `Social Security Difference`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Awards IN __ OUT' THEN tsd.amount END) AS `Awards IN-OUT`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Vacation allowance - current year' THEN tsd.amount END) AS `Vacation Allowance-Current Year`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Vacation allowance - past year' THEN tsd.amount END) AS `Vacation Allowance-Past Year`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Health  Insurance' THEN tsd.amount END) AS `Health  Insurance`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Health Insurance Fees' THEN tsd.amount END) AS `Health Insurance Fees`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Hussein Cancer Center Donation' THEN tsd.amount END) AS `Hussein Cancer Center Donation`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Bonus IN-OUT' THEN tsd.amount END) AS `Bonus IN-OUT`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Catering Deduction' THEN tsd.amount END) AS `Catering Deduction`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Jordan Engineers Association subscriptions and loans' THEN tsd.amount END) AS `Jordan Engineers Association Subscriptions and loans`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Penalty as per Jordan Labor Law' THEN tsd.amount END) AS `Penalty as per Jordan Labor Law`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Penalty Internal Law' THEN tsd.amount END) AS `Penalty Internal Law`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Safety Violation' THEN tsd.amount END) AS `Safety Violation`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Salary Differences - Deduction' THEN tsd.amount END) AS `Salary Differences-Deduction`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Traffic Violation' THEN tsd.amount END) AS `Traffic Violation`,
	# 								MAX(CASE WHEN tsd.salary_component = 'Warehouse custody allowance' THEN tsd.amount END) AS `Warehouse Custody Allowance`,
	# 								MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`
									
	# 						FROM `tabSalary Slip` tss
	# 						INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
	# 						INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
	# 						INNER JOIN `tabEmployee` te ON te.name = tss.employee
	# 						INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
	# 						WHERE tss.docstatus = 1 AND  tss_sub.name = tss.name
	# 									And (tss.posting_date BETWEEN '{_from}' AND '{to}')
	# 									{conditions}
	# 									GROUP BY tss.name, tss.employee, tss.employee_name, tss.department,
	# 									tss.designation, te.date_of_joining, tssa.base;""")

	# return data

	data = frappe.db.sql(f"""select te.name AS `Employee No.`, te.employee_name AS `Employee Name`, te.date_of_joining AS `Date of Joining`, te.work_type AS `Work Type`, tss.company AS `Company`,
									te.branch AS `Branch`, te.department AS `Department`, te.designation AS `Designation`, 
									tssa.base AS `Basic Salary`,
									MAX(CASE WHEN tsd.salary_component = 'Transportation' THEN tsd.amount END) AS `Transportation`,
									MAX(CASE WHEN tsd.salary_component = 'Expatriate Allowance' THEN tsd.amount END) AS `Expatriate Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Mobile Allowance' THEN tsd.amount END) AS `Mobile Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Field Allowance' THEN tsd.amount END) AS `Field Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Housing' THEN tsd.amount END) AS `Housing`,
									MAX(CASE WHEN tsd.salary_component = 'Work days allowance' THEN tsd.amount END) AS `Work Days Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Project Awards' THEN tsd.amount END) AS `Project Awards`,
									MAX(CASE WHEN tsd.salary_component = 'Fixed Allowance' THEN tsd.amount END) AS `Fixed Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Fuel Allowance' THEN tsd.amount END) AS `Fuel Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Fund Allowance' THEN tsd.amount END) AS `Fund Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Master Degree Allowance' THEN tsd.amount END) AS `Master Degree Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Board Allowance' THEN tsd.amount END) AS `Board Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Children Education Allowance' THEN tsd.amount END) AS `Children Education Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'End Service Awards' THEN tsd.amount END) AS `End Service Awards`,
									MAX(CASE WHEN tsd.salary_component = 'Award' THEN tsd.amount END) AS `Award`,
									MAX(CASE WHEN tsd.salary_component = 'Arrear' THEN tsd.amount END) AS `Arrear`,
									MAX(CASE WHEN tsd.salary_component = 'Leave Encashment' THEN tsd.amount END) AS `Leave Encashment`,
									MAX(CASE WHEN tsd.salary_component = 'Medical Treatment Allowance' THEN tsd.amount END) AS `Medical Treatment Allowance`,
									MAX(CASE WHEN tsd.salary_component = 'Non Taxable Bonus' THEN tsd.amount END) AS `Non Taxable Bonus`,
									MAX(CASE WHEN tsd.salary_component = 'Notice Period' THEN tsd.amount END) AS `Notice Period`,
									MAX(CASE WHEN tsd.salary_component = 'Refunds' THEN tsd.amount END) AS `Refunds`,
									MAX(CASE WHEN tsd.salary_component = 'Salaries Differences - Earning' THEN tsd.amount END) AS `Salaries Differences-Earning`,
									MAX(CASE WHEN tsd.salary_component = 'Social Security Difference' THEN tsd.amount END) AS `Social Security Difference`,
									MAX(CASE WHEN tsd.salary_component = 'Awards IN __ OUT' THEN tsd.amount END) AS `Awards IN-OUT`,
									MAX(CASE WHEN tsd.salary_component = 'Vacation allowance - current year' THEN tsd.amount END) AS `Vacation Allowance-Current Year`,
									MAX(CASE WHEN tsd.salary_component = 'Vacation allowance - past year' THEN tsd.amount END) AS `Vacation allowance-Past Year`,
									MAX(CASE WHEN tsd.salary_component = 'Vehicle Use Allowance' THEN tsd.amount END) AS `Vehicle Use Allowance`,
									 te.social_security_amount AS `Social Security`,
									MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
									MAX(CASE WHEN tsd.salary_component = 'Health  Insurance' THEN tsd.amount END) AS `Health  Insurance`,
									MAX(CASE WHEN tsd.salary_component = 'Health Insurance Fees' THEN tsd.amount END) AS `Health Insurance Fees`,
									MAX(CASE WHEN tsd.salary_component = 'Hussein Cancer Center Donation' THEN tsd.amount END) AS `Hussein Cancer Center Donation`,
									MAX(CASE WHEN tsd.salary_component = 'Bonus IN-OUT' THEN tsd.amount END) AS `Bonus IN-OUT`,
									MAX(CASE WHEN tsd.salary_component = 'Catering Deduction' THEN tsd.amount END) AS `Catering Deduction`,
									MAX(CASE WHEN tsd.salary_component = 'Jordan Engineers Association subscriptions and loans' THEN tsd.amount END) AS `Jordan Engineers Association Subscriptions & Loans`,
									MAX(CASE WHEN tsd.salary_component = 'Penalty as per Jordan Labor Law' THEN tsd.amount END) AS `Penalty as Per Jordan Labor Law`,
									MAX(CASE WHEN tsd.salary_component = 'Penalty Internal Law' THEN tsd.amount END) AS `Penalty Internal Law`,
									MAX(CASE WHEN tsd.salary_component = 'Safety Violation' THEN tsd.amount END) AS `Safety Violation`,
									MAX(CASE WHEN tsd.salary_component = 'Salary Differences - Deduction' THEN tsd.amount END) AS `Salary Differences-Deduction`,
									MAX(CASE WHEN tsd.salary_component = 'Traffic Violation' THEN tsd.amount END) AS `Traffic Violation`,
									MAX(CASE WHEN tsd.salary_component = 'Warehouse custody allowance' THEN tsd.amount END) AS `Warehouse cCustody Allowance`
									-- MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`
									from `tabSalary Structure` tss 
									inner join `tabSalary Structure Assignment` tssa on tss.name = tssa.salary_structure 
									INNER join `tabSalary Detail` tsd on tsd.parent  = tss.name
									inner join `tabSalary Component` tsc on tsd.salary_component = tsc.name
									inner join `tabEmployee` te on tssa.employee = te.name 
									INNER JOIN `tabEmployee Social Security Salary` tesss on te.name = tesss.employee 
								WHERE tssa.docstatus = 1
										{conditions}
								GROUP BY tss.name, tssa.employee, tssa.base, te.social_security_amount;""")

	return data
















def get_columns():
	return [
	   "Employee No.:Link/Employee:200",
	   "Employee Name: Data:200",
	   "Date of Joining: Data:200 ",
 	   "Work Type: Data:200",
	   "Company: Data:300",
	   "Branch: Data:200",
	   "Department: Data:200",
	   "Designation: Data:200",
	   "Basic Salary: Data:200",
	   "Transportation: Data:200",
	   "Expatriate Allowance: Data:200",
	   "Mobile Allowance: Data:200",
	   "Overtime Allowance: Data:200",
	   "Field Allowance: Data:200",
	   "Housing: Data:200",
	   "Work Days Allowance: Data:200",
	   "Project Awards: Data:200",
	   "Fixed Allowance: Data:200",
	   "Fuel Allowance: Data:200",
	   "Fund Allowance: Data:200",
	   "Master Degree Allowance: Data:200",
	   "Board Allowance: Data:200",
	   "Children Education Allowance: Data:200",
	   "End Service Awards: Data:200",
	   "Award: Data:200",
	   "Arrear: Data:200",
	   "Leave Encashment:200",
	   "Medical Treatment Allowance: Data:200",
	   "Non Taxable Bonus: Data:200",
	   "Notice Period: Data:200",
	   "Refunds: Data:200",
	   "Salaries Differences-Earning: Data:200",
	   "Social Security Difference:200",
	   "Awards IN-OUT: Data:200",
	   "Vacation Allowance-Current Year: Data:200",
	   "Vacation Allowance Past Year:200",
	   "Vehicle Use Allowance: Data:200",
	   "Social Security: Data:200",
	   "Income Tax: Data:200",
	   "Health  Insurance: Data:200",
	   "Health Insurance Fees: Data:200",
	   "Hussein Cancer Center Donation: Data:200",
	   "Bonus IN-OUT: Data:200",
	   "Catering Deduction: Data:200",
	   "Jordan Engineers Association Subscriptions & loans: Data:200",
	   "Penalty as per Jordan Labor Law: Data:200",
	   "Penalty Internal Law:200",
	   "Safety Violation: Data:200",
	   "Salary Differences-Deduction: Data:200",
	   "Traffic Violation: Data:200",
	   "Warehouse Custody Allowance: Data:200"
	#    "Loan: Data:200"
	   

	]
