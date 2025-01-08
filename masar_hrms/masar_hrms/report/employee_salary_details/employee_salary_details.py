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
	if(filters.get('is_hazard')):conditions += f" AND te.custom_is_hazard = '{filters.get('is_hazard')}'"

	#SQL Query
	data = frappe.db.sql(f"""
		SELECT DISTINCT
			tss.name AS `Salary Slip No.`,
			tss.employee AS `Employee No.`,
			tss.employee_name AS `Employee Name`,
			tss.branch AS `Branch`,
			te.work_type AS `Work Type`,
			tss.company AS `Company`,
			tss.department AS `Department`,
			tss.designation AS `Designation`,
			te.date_of_joining AS `Date of Joining`,
			te.custom_is_hazard AS `Is Hazard`,
			tss.gross_pay AS `Reserved Salary`,
			tss.leave_without_pay AS `Leave Without Pay`,
			tss.payment_days AS `Payment Days`,
			MAX(CASE WHEN tsd.salary_component = 'Basic' THEN tsd.amount END) AS `Basic Salary`,
			tssa.base AS `Original Basic Salary`,
			MAX(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
			MAX(CASE WHEN tsd.salary_component IN ('Awards IN __ OUT', 'Non Taxable Bonus', 'End Service Awards', 'Project Awards', 'Award', 'Bonus IN-OUT') THEN tsd.amount END) AS `Awards`,
			MAX(CASE WHEN tsd.salary_component = 'Arrear' THEN tsd.amount END) AS `Arrear`,
			MAX(CASE WHEN tsd.salary_component = 'Specialty Allowance' THEN tsd.amount END) AS `Specialty Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Fuel Allowance' THEN tsd.amount END) AS `Fuel Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Other Allowance' THEN tsd.amount END) AS `Other Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Other Income' THEN tsd.amount END) AS `Other Income`,
			MAX(CASE WHEN tsd.salary_component = 'Notice Period' THEN tsd.amount END) AS `Notice Period`,
			MAX(CASE WHEN tsd.salary_component = 'Schooling' THEN tsd.amount END) AS `Schooling`,
			MAX(CASE WHEN tsd.salary_component = 'Board Allowance' THEN tsd.amount END) AS `Board Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Field Allowance' THEN tsd.amount END) AS `Field Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Mobile Allowance' THEN tsd.amount END) AS `Mobile Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Master Degree Allowance' THEN tsd.amount END) AS `Master Degree Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Housing' THEN tsd.amount END) AS `Housing`,
			MAX(CASE WHEN tsd.salary_component = 'Expatriate Allowance' THEN tsd.amount END) AS `Expatriate Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Transportation' THEN tsd.amount END) AS `Transportation`,
			MAX(CASE WHEN tsd.salary_component = 'Vehicle Allowance' THEN tsd.amount END) AS `Vehicle Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Vehicle Use Allowance' THEN tsd.amount END) AS `Vehicle Use Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Site Allowance' THEN tsd.amount END) AS `Site Allowance`,
			MAX(CASE WHEN tsd.salary_component = 'Leave Encashment' THEN tsd.amount END) AS `Leave Encashment`,
			tss.gross_pay AS `Total Earnings`,
			te.social_security_salary AS `Social Security Salary`,
			MAX(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
			CASE 
				WHEN tss.payment_days < 16 THEN 0
				ELSE 
					CASE 
						WHEN te.custom_is_hazard = 1 THEN IFNULL(te.social_security_salary, 0) * 0.15250 
						ELSE IFNULL(te.social_security_salary, 0) * 0.14250 
					END
			END AS `Social Security Company Share`,
			MAX(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
			MAX(CASE WHEN tsd.salary_component = 'Other Deduction' THEN tsd.amount END) AS `Other Deduction`,
			MAX(CASE WHEN tsd.salary_component = 'Catering Deduction' THEN tsd.amount END) AS `Catering Deduction`,
			MAX(CASE WHEN tsd.salary_component = 'Health Insurance Fees' THEN tsd.amount END) AS `Health Insurance Fees`,
			MAX(CASE WHEN tsd.salary_component = 'Hussein Cancer Center Donation' THEN tsd.amount END) AS `Hussein Cancer Center Donation`,
			MAX(CASE WHEN tsd.salary_component = 'Penalty Internal Law' THEN tsd.amount END) AS `Penalty Internal Law`,
			MAX(CASE WHEN tsd.salary_component = 'Traffic Violation' THEN tsd.amount END) AS `Traffic Violation`,
			MAX(CASE WHEN tsd.salary_component = 'Jordan Engineers Association subscriptions and loans' THEN tsd.amount END) AS `Jordan Engineers Association subscriptions and loans`,
			MAX(CASE WHEN tsd.salary_component = 'Loan' THEN tsd.amount END) AS `Loan`,
			MAX(CASE WHEN tsd.salary_component = 'Attendance Shortage' THEN tsd.amount END) AS `Attendance Shortage`,
			tss.total_deduction AS `Total Deductions`,
			tss.net_pay AS `Net Pay`,
			te.old_ref AS `Old Reference`,
			DATE_FORMAT(tss.start_date , '%M') as `Posting Month` , 
			tss.mode_of_payment AS `Mode Of Payment`
		FROM
			`tabSalary Slip` tss
		INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
		INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
		INNER JOIN `tabEmployee` te ON te.name = tss.employee
		INNER JOIN `tabSalary Slip` tss_sub ON tss_sub.name = tss.name
		WHERE
			tss.docstatus = 1 AND tss_sub.name = tss.name AND tssa.docstatus = 1
			And (tss.start_date BETWEEN '{_from}' AND '{to}') {conditions}
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
		"Is Hazard: Check:100",
    #    "Month: Data:80",
	   "Reserved Salary: Currency:150",
	   "Leave Without Pay: Data:150",
	   #"Absent Days: Data:200",
	   "Payment Days: Data:150",
	#    "Reserved Basic Salary: Currency:150",
	 	"Basic Salary: Currency:150",
		"Original Basic Salary: Currency:150",
	   "Overtime Allowance: Currency:150",
	   "Awards: Currency:150",
		"Arrear: Currency:150",
		"Specialty Allowance: Currency:150",
		"Fuel Allowance: Currency:150",
		"Other Allowance: Currency:150",
		"Other Income: Currency:150",
		"Notice Period: Currency:150",
		"Schooling: Currency:150",
		"Board Allowance: Currency:150",
		"Field Allowance: Currency:150",
		"Mobile Allowance: Currency:150",
		"Master Degree Allowance: Currency:150",
		"Housing: Currency:150",
		"Expatriate Allowance: Currency:150",
		"Transportation: Currency:150",
		"Vehicle Allowance: Currency:150",
		"Vehicle Use Allowance: Currency:150",
		"Site Allowance: Currency:150",
		"Leave Encashment: Currency:150",
	   "Total Earnings: Currency:150",
		"Social Security Salary: Currency:150",
	   "Social Security: Currency:150",
		"Social Security Company Share: Currency:150",
	   "Income Tax: Currency:150",
	   #"Loan: Currency:200",
	   "Other Deduction: Currency:150",
       "Catering Deduction: Currency:150",
       "Health Insurance Fees: Currency:150",
       "Hussein Cancer Center Donation: Currency:150",
       "Penalty Internal Law: Currency:150",
       "Traffic Violation: Currency:150",
       "Jordan Engineers Association subscriptions and loans: Currency:150",
       "Loan: Currency:150",
       "Attendance Shortage: Currency:150",
	   "Total Deductions: Currency:150",
	   "Net Pay: Currency:150",
	   "Old Reference: Data:150",
	   "Posting Month: Data/Posting Month:150",
	   "Mode Of Payment: Data/Mode Of Paymnet:150" 

	   # "Tax Group: Data:200",
	   # "Currency Code: Data:200"
	   #"Status:150"
	]
# to add loan in the report siam
# MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,