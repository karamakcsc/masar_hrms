# Copyright (c) 2023, KCSC and contributors
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
	if(filters.get('ss_no')):conditions += f" AND tss.name LIKE '%{filters.get('ss_no')}' "
	if(filters.get('company')):conditions += f" AND tss.company='{filters.get('company')}' "
	if(filters.get('emp_name')):conditions += f" AND tss.employee LIKE '%{filters.get('emp_name')}' "
	if(filters.get('des')):conditions += f" AND tss.designation LIKE '%{filters.get('des')}' "
	if(filters.get('work_type')):conditions += f" AND tss.work_type='{filters.get('work_type')}' "
	if(filters.get('branch')):conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
	if(filters.get('dep')):conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "
	if(filters.get('is_hazard')):conditions += f" AND te.custom_is_hazard = '{filters.get('is_hazard')}'"
 
	components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])
	earnings = sorted([c.name for c in components if c.type == "Earning"])
	deductions = sorted([c.name for c in components if c.type == "Deduction"])
 
	earnings_set = set()
	basic_sql = ""
	for comp in earnings:
		if comp == "Basic":
			basic_sql = f"MAX(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"
			earnings_set.add(comp)
   
	earning_comps = ""
	for comp in earnings:
		if comp not in earnings_set:
			earning_comps += f"MAX(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"
	
	deductions_set = set()
	ss_sql = ""
	for comp in deductions:
		if comp == "Social Security":
			ss_sql = f"MAX(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"
			deductions_set.add(comp)
   
	deduction_comps = ""
	for comp in deductions:
		if comp not in deductions_set:
			deduction_comps += f"MAX(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"

	#SQL Query
	data = frappe.db.sql(f"""
		SELECT DISTINCT
			tss.name AS `Salary Slip No.`,
			tss.employee AS `Employee No.`,
			tss.employee_name AS `Employee Name`,
			tss.branch AS `Branch`,
			tss.work_type AS `Work Type`,
			tss.company AS `Company`,
			tss.department AS `Department`,
			tss.designation AS `Designation`,
			te.date_of_joining AS `Date of Joining`,
			te.custom_is_hazard AS `Is Hazard`,
			tss.gross_pay AS `Reserved Salary`,
			tss.leave_without_pay AS `Leave Without Pay`,
			tss.payment_days AS `Payment Days`,
			{basic_sql}
			{earning_comps}
			tss.gross_pay AS `Total Earnings`,
			te.social_security_salary AS `Social Security Salary`,
			{ss_sql}
			CASE 
				WHEN tss.payment_days < 16 THEN 0
				ELSE 
					CASE 
						WHEN te.custom_is_hazard = 1 THEN IFNULL(te.social_security_salary, 0) * 0.15250 
						ELSE IFNULL(te.social_security_salary, 0) * 0.14250 
					END
			END AS `Social Security Company Share`,
			{deduction_comps}
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
			tss.name, tss.net_pay
			;
		""")

	return data

def get_columns():
	columns = [
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
		"Reserved Salary: Currency:150",
		"Leave Without Pay: Data:150",
		"Payment Days: Data:150",
	]
	components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])

	earnings = sorted([c.name for c in components if c.type == "Earning"])
	deductions = sorted([c.name for c in components if c.type == "Deduction"])
 
 
	earnings_set = set()
	for comp in earnings:
		if comp == "Basic":
			columns.append(f"{comp}:Data:200")
			earnings_set.add(comp)
   
	for comp in earnings:
		if comp not in earnings_set:
			columns.append(f"{comp}:Data:200")
	
	columns += [
		"Total Earnings: Currency:150",
		"Social Security Salary: Currency:150",
	]
	
	deductions_set = set()
	for comp in deductions:
		if comp == "Social Security":
			columns.append(f"{comp}:Data:200")
			deductions_set.add(comp)
  
	columns += [
		"Social Security Company Share: Currency:150",
	]
 
	for comp in deductions:
		if comp not in deductions_set:
			columns.append(f"{comp}:Data:200")
	
	columns += [
		"Total Deductions: Currency:150",
		"Net Pay: Currency:150",
		"Old Reference: Data:150",
		"Posting Month: Data/Posting Month:150", 
		"Mode of Payment: Data/Mode of Payment"
	]
 
	return columns
# to add loan in the report siam
# MAX(CASE WHEN tss.total_loan_repayment > 0 THEN tss.total_loan_repayment ELSE 0 END) AS `Loan`,