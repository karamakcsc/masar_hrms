# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    _from, to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND te.name = '{filters.get('employee')}'"
    if filters.get('department'):
        conditions += f" AND te.department = '{filters.get('department')}'"
    if _from and to:
        conditions += f" AND tss.posting_date BETWEEN '{_from}' AND '{to}'"
    
    
    sql = frappe.db.sql(f"""
                    WITH emp_salary AS (
						SELECT
							te.name AS employee,
							MAX(CASE
								WHEN tsd.salary_component = 'Income Tax'
								THEN tsd.amount
							END) AS `income_tax`
						FROM `tabEmployee` te
						LEFT JOIN 
							`tabSalary Slip` tss ON tss.employee = te.name 
						LEFT JOIN 
							`tabSalary Detail` tsd ON tsd.parent = tss.name 
						GROUP BY tss.name
					)
					SELECT DISTINCT
						te.name AS `Employee No.`, 
						te.full_name_ar AS `Employee Name`, 
						COALESCE(te.national_no, te.passport_number) AS `National No. / Passport No.`,
						te.nationality AS `Nationality`, 
						SUM(CASE WHEN tsd.salary_component = 'Basic' THEN tsd.amount END) AS `Total Salary`, 
						CASE WHEN te.name != NULL THEN 0 END AS `Non Monthly Salary`,
						SUM(CASE WHEN tsd.salary_component = 'Award' THEN tsd.amount END) AS `Management Awards`,
						SUM(CASE WHEN tsd.salary_component = 'End Service Awards' THEN tsd.amount END) AS `EOS Salary`,
						SUM(CASE WHEN tsd.salary_component NOT IN ('Basic', 'Other Allowance', 'Award', 'End Service Awards') AND tsd.parentfield = 'earnings' THEN tsd.amount END) AS `Other Earnings`,
						SUM(CASE WHEN tsd.salary_component = 'Social Security' THEN tsd.amount END) AS `Social Security`,
						SUM(CASE WHEN tsd.salary_component = 'Income Tax' THEN tsd.amount END) AS `Income Tax`,
						SUM(CASE WHEN tsd.salary_component != 'Social Security' AND tsd.parentfield = 'deductions' THEN tsd.amount END) AS `Other Deductions`,
						MAX(tss.year_to_date) AS `Total Net Pay`,
						TIMESTAMPDIFF(MONTH, te.date_of_joining, MAX(tss.posting_date)) AS `Working Months`,
						(CASE 
								WHEN (es.income_tax = 0 AND te.marital_status = 'Single') 
								THEN 'Exempt Single'
								WHEN (es.income_tax = 0 AND te.marital_status = 'Married') 
								THEN 'Exempt Married'
								WHEN (es.income_tax = 0 AND te.marital_status NOT IN ('Single', 'Married'))
								THEN 'Exempt Other'
								ELSE 'Not Exempt'
						END) AS `Exemption`
					FROM 
						tabEmployee te
					LEFT JOIN 
						`tabSalary Slip` tss ON tss.employee = te.name 
					LEFT JOIN 
						`tabSalary Detail` tsd ON tsd.parent = tss.name 
					INNER JOIN 
						`tabEmployee Salary Table` test ON test.parent = te.name
					LEFT JOIN
						emp_salary es ON es.employee = te.name
					WHERE 
						{conditions} AND te.status = 'Active' 
					GROUP BY 
						te.employee,
						te.full_name_ar, 
						te.national_no, 
						te.nationality, 
						te.date_of_joining,
						te.marital_status
				""")
    
    return sql

def get_columns():
    return [
		"Employee No.: Link/Employee:200",
	    "Employee Name: Data:250",
	    "National No. / Passport No.: Data:250", 
	    "Nationality: Data:100",
	    "Total Salary: Currency:200",
		"Non Monthly Salary: Currency:200",
		"Management Awards: Currency:200",
		"EOS Salary: Currency:200",
		"Other Earnings: Currency:200",
		"Social Security: Currency:200",
		"Income Tax: Currency:200",
		"Other Deductions: Currency:200",
  		"Total Net Pay: Currency:200",
		"Working Months: Float:200",
		"Exemption: Data:200",
	]