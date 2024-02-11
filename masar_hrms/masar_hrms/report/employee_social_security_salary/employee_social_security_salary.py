from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	_from, to = filters.get('from'), filters.get('to') #date range # date range

    # Conditions
	conditions = ""
	if filters.get('emp_name'):
		conditions += f" AND te.employee = '{filters.get('emp_name')}' "
	data = frappe.db.sql(f"""
			SELECT
                tss.employee AS `Employee No.`,
                te.employee_name AS `Employee Name`,
                te.social_security_number AS `Social Security Number` , 
                te.social_security_date AS `Social Security Date` , 
                te.social_security_amount AS `Social Security Amount` ,
                tssa.base AS `Basic Salary`,
                COALESCE(SUM(CASE WHEN tsd.parentfield = 'earnings' AND tsd.salary_component != 'Basic' THEN tsd.amount ELSE 0 END), 0) AS `Other Earnings`,
                tss.posting_date AS `Posting Date`
            FROM
                `tabSalary Slip` tss
                INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
                INNER JOIN `tabSalary Structure Assignment` tssa ON tssa.employee = tss.employee
                INNER JOIN `tabEmployee` te ON te.name = tss.employee
                INNER JOIN `tabSalary Structure` tss2 ON tss2.name = tssa.salary_structure 
                INNER JOIN `tabSalary Component` tsc ON tsd.salary_component = tsc.name
            WHERE
                tss.docstatus = 1 
				AND tssa.docstatus = 1 
				AND tss2.is_active = 'Yes' 
				AND tsc.is_social_security_applicable = 1
				AND tss.posting_date BETWEEN '{_from}' AND '{to}'
				{conditions} 
            GROUP BY
                tss.name, tss.employee, te.employee_name, tssa.base, tss.posting_date;
    """)
	return data

def get_columns():
	return [
	   "Employee No.:Link/Employee:200",
	   "Employee Name: Data:200",
	   "Social Security Number : data :200", 
	   "Social Security Date : data :200" ,
	   "Social Security Amount : data : 200",
	   "Basic Salary: data:150",
	   "Other Earnings: Currency:150",
	   "Posting Date: data:150",

	]
