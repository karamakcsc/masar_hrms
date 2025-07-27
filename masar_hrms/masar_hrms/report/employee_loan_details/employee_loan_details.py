# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    if filters.get("employee"):
        conditions += f" AND tel.employee = '{filters.get('employee')}'"
    if filters.get("department"):
        conditions += f" AND tel.department = '{filters.get('department')}'"
    if filters.get("designation"):
        conditions += f" AND tel.designation = '{filters.get('designation')}'"
    
    sql = frappe.db.sql(f"""
        SELECT
			tel.name AS `Loan ID`,
			tel.employee AS `Employee ID`,
			tel.employee_name AS `Employee Name`,
			tel.department AS `Department`,
			tel.designation AS `Designation`,
			tel.start_date AS `Loan Start Date`,
			tel.end_date AS `Loan End Date`,
			tel.loan_amount AS `Total Loan Amount`,
			IFNULL(SUM(tas.amount), 0) AS `Repaid Amount`,
			(tel.loan_amount - IFNULL(SUM(tas.amount), 0)) AS `Remaining Amount`,
			MAX(tas.payroll_date) AS `Latest Payment Date`
		FROM
			`tabEmployee Loans` tel
		LEFT JOIN
			`tabEmployee Loans Schedule` tels ON tels.parent = tel.name
		LEFT JOIN
			`tabAdditional Salary` tas ON tas.name = tels.additional_salary_ref
			AND tas.docstatus = 1
			AND tas.salary_component = 'Loan'
			AND tas.payroll_date BETWEEN tel.start_date AND CURDATE()
		WHERE
			{conditions} AND tel.docstatus = 1
		GROUP BY
			tel.name
		ORDER BY
			tel.employee_name;
	""")
    
    return sql

def get_columns():
    	return [
		{"label": "Loan ID", "fieldname": "Loan ID", "fieldtype": "Data", "width": 120},
		{"label": "Employee ID", "fieldname": "Employee ID", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "Employee Name", "fieldname": "Employee Name", "fieldtype": "Data", "width": 150},
		{"label": "Department", "fieldname": "Department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": "Designation", "fieldname": "Designation", "fieldtype": "Link", "options": "Designation", "width": 150},
		{"label": "Loan Start Date", "fieldname": "Loan Start Date", "fieldtype": "Date", "width": 120},
		{"label": "Loan End Date", "fieldname": "Loan End Date", "fieldtype": "Date", "width": 120},
		{"label": "Total Loan Amount", "fieldname": "Total Loan Amount", "fieldtype": "Currency", 
			"options":"currency" , 'width': 150},
		{"label": "Repaid Amount", 
			"fieldname":"Repaid Amount",
			"fieldtype":"Currency",
			"options":"currency",
			'width': 150},
		{"label":"Remaining Amount",
			"fieldname":"Remaining Amount",
			"fieldtype":"Currency",
			"options":"currency",
			'width': 150},
		{"label":"Latest Payment Date",
			'fieldname':"Latest Payment Date",
			'fieldtype':"Date",
			'width':120}
	]