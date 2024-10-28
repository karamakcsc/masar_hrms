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
	if(filters.get('employee')):conditions += f" AND te.employee = '{filters.get('employee')}' "
	if(filters.get('s_component')):conditions += f" AND test.salary_component = '{filters.get('s_component')}' "
	if(_from and to): conditions += f" AND test.date BETWEEN '{_from}' AND '{to}'"
	#SQL Query
	data = frappe.db.sql(f"""
					SELECT
						te.name AS `Employee`, 
						te.employee_name AS `Employee Name`, 
						test.salary_component AS `Salary Component`,
						test.is_active AS `Is Active`, 
						test.esc_amount AS `Amount`,
						test.`date` AS `Date`, 
						test.remarks AS `Remarks`
					FROM 
						tabEmployee te
					INNER JOIN 
						`tabEmployee Salary Table` test ON test.parent = te.name
					INNER JOIN 
						`tabSalary Component` tsc ON test.salary_component = tsc.salary_component
					WHERE 
						tsc.`type` = 'Earning' {conditions}
      				ORDER BY
          				te.employee ASC;
			""")

	return data

def get_columns():
	return [
	   "Employee: Link/Employee:200",
	   "Employee Name: Data:200",
	   "Salary Component: Link/Salary Component:200",
	   "Is Active: Check:100",
	   "Amount: Currency:200",
	   "Date: Date:200",
	   "Remarks: Data:250"
	]
