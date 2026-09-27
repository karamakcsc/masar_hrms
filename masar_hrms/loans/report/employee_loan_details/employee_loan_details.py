# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data)


def get_conditions(filters):
	conditions = " 1=1 "
	if filters.get("employee"):
		conditions += " AND tel.employee = %(employee)s"
	if filters.get("department"):
		conditions += " AND tel.department = %(department)s"
	if filters.get("designation"):
		conditions += " AND tel.designation = %(designation)s"
	return conditions


def get_data(filters):
    conditions = get_conditions(filters)

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
	""", filters)

    return sql


def get_chart(data):
	# `data` rows are already grouped one-per-loan by get_data(), so summing
	# "Total Loan Amount"/"Repaid Amount" here avoids re-joining the schedule
	# and additional salary tables (which would fan out and double-count).
	total_loan = sum(row[7] or 0 for row in data)
	total_repaid = sum(row[8] or 0 for row in data)
	total_remaining = total_loan - total_repaid

	if not total_loan:
		return None

	return {
		"data": {
			"labels": [_("Repaid"), _("Remaining")],
			"datasets": [{"name": _("Amount"), "values": [total_repaid, total_remaining]}],
		},
		"type": "donut",
		"colors": ["#28a745", "#dc3545"],
		"height": 280,
	}

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