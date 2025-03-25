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
	conditions = " AND 1=1 "
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('work_type')):conditions += f" AND tss.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "

	#SQL Query
	data = frappe.db.sql(f"""
        WITH base_amounts AS ( -- sum the salary slip fields before the components to avoid duplications
            SELECT -- because if there are 10 components the salary slip field will be summed 10 times
                DATE_FORMAT(tss.start_date, '%Y-%m') AS month,
                tss.work_type,
                tss.company,
                SUM(tss.gross_pay) AS total_gross_pay,
                SUM(tss.total_deduction) AS total_deductions,
                SUM(tss.net_pay) AS total_net_pay
            FROM `tabSalary Slip` tss
            WHERE tss.docstatus = 1 
            AND (tss.start_date BETWEEN '{_from}' AND '{to}') {conditions}
            GROUP BY DATE_FORMAT(tss.start_date, '%Y-%m'), tss.work_type, tss.company
        )
        SELECT 
            ba.month AS `Month`,
            ba.work_type AS `Work Type`,
            ba.company AS `Company`,
            ba.total_gross_pay AS `Reserved Salary`,
            SUM(CASE WHEN tsd.salary_component = 'Basic' THEN tsd.amount END) AS `Basic Salary`,
            SUM(CASE WHEN tsd.salary_component = 'Overtime Allowance' THEN tsd.amount END) AS `Overtime Allowance`,
            SUM(CASE WHEN tsd.salary_component IN ('Awards IN __ OUT', 'Non Taxable Bonus', 'End Service Awards', 'Project Awards', 'Award', 'Bonus IN-OUT') THEN tsd.amount END) AS `Awards`,
            SUM(CASE WHEN tsd.salary_component = 'Arrear' THEN tsd.amount END) AS `Arrear`,
            SUM(CASE WHEN tsd.salary_component = 'Specialty Allowance' THEN tsd.amount END) AS `Specialty Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Fuel Allowance' THEN tsd.amount END) AS `Fuel Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Other Allowance' THEN tsd.amount END) AS `Other Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Other Income' THEN tsd.amount END) AS `Other Income`,
            SUM(CASE WHEN tsd.salary_component = 'Notice Period' THEN tsd.amount END) AS `Notice Period`,
            SUM(CASE WHEN tsd.salary_component = 'Schooling' THEN tsd.amount END) AS `Schooling`,
            SUM(CASE WHEN tsd.salary_component = 'Board Allowance' THEN tsd.amount END) AS `Board Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Field Allowance' THEN tsd.amount END) AS `Field Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Mobile Allowance' THEN tsd.amount END) AS `Mobile Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Master Degree Allowance' THEN tsd.amount END) AS `Master Degree Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Housing' THEN tsd.amount END) AS `Housing`,
            SUM(CASE WHEN tsd.salary_component = 'Expatriate Allowance' THEN tsd.amount END) AS `Expatriate Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Transportation' THEN tsd.amount END) AS `Transportation`,
            SUM(CASE WHEN tsd.salary_component = 'Vehicle Allowance' THEN tsd.amount END) AS `Vehicle Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Vehicle Use Allowance' THEN tsd.amount END) AS `Vehicle Use Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Site Allowance' THEN tsd.amount END) AS `Site Allowance`,
            SUM(CASE WHEN tsd.salary_component = 'Leave Encashment' THEN tsd.amount END) AS `Leave Encashment`,
            ba.total_gross_pay AS `Total Earnings`,
            SUM(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
            SUM(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
            SUM(CASE WHEN tsd.salary_component = 'Other Deduction' THEN tsd.amount END) AS `Other Deduction`,
            SUM(CASE WHEN tsd.salary_component = 'Catering Deduction' THEN tsd.amount END) AS `Catering Deduction`,
            SUM(CASE WHEN tsd.salary_component = 'Health Insurance Fees' THEN tsd.amount END) AS `Health Insurance Fees`,
            SUM(CASE WHEN tsd.salary_component = 'Hussein Cancer Center Donation' THEN tsd.amount END) AS `Hussein Cancer Center Donation`,
            SUM(CASE WHEN tsd.salary_component = 'Penalty Internal Law' THEN tsd.amount END) AS `Penalty Internal Law`,
            SUM(CASE WHEN tsd.salary_component = 'Traffic Violation' THEN tsd.amount END) AS `Traffic Violation`,
            SUM(CASE WHEN tsd.salary_component = 'Jordan Engineers Association subscriptions and loans' THEN tsd.amount END) AS `Jordan Engineers Association subscriptions and loans`,
            SUM(CASE WHEN tsd.salary_component = 'Loan' THEN tsd.amount END) AS `Loan`,
            SUM(CASE WHEN tsd.salary_component = 'Attendance Shortage' THEN tsd.amount END) AS `Attendance Shortage`,
            ba.total_deductions AS `Total Deductions`,
            ba.total_net_pay AS `Net Pay`
        FROM base_amounts ba -- connects the firs query
        LEFT JOIN `tabSalary Slip` tss ON DATE_FORMAT(tss.start_date, '%Y-%m') = ba.month 
            AND tss.work_type = ba.work_type 
            AND tss.company = ba.company
            AND tss.docstatus = 1
        LEFT JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
        WHERE (tss.start_date BETWEEN '{_from}' AND '{to}') {conditions}
        GROUP BY ba.month, ba.work_type, ba.company
        ORDER BY ba.month ASC
		""")

	return data

def get_columns():
	return [
	   "Month: Date:200",
	   "Work Type: Data:200",
	   "Company: Data:300",
	   "Reserved Salary: Currency:150",
	 	"Basic Salary: Currency:150",
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
	   "Social Security: Currency:150",
	   "Income Tax: Currency:150",
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
	]
# to add loan in the report siam
# MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,