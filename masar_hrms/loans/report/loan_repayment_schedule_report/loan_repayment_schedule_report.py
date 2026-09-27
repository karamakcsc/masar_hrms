# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_conditions(filters):
	conditions = " 1=1 "
	if filters.get("employee"):
		conditions += " AND tel.employee = %(employee)s"
	if filters.get("department"):
		conditions += " AND tel.department = %(department)s"
	if filters.get("from_date"):
		conditions += " AND tels.schedule_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND tels.schedule_date <= %(to_date)s"
	if filters.get("status") == "Paid":
		conditions += " AND tas.name IS NOT NULL AND tas.docstatus = 1"
	if filters.get("status") == "Unpaid":
		conditions += " AND (tas.name IS NULL OR tas.docstatus != 1)"
	return conditions


def get_data(filters):
	conditions = get_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			tel.name AS `Loan ID`,
			tel.employee AS `Employee ID`,
			tel.employee_name AS `Employee Name`,
			tel.department AS `Department`,
			tels.schedule_date AS `Schedule Date`,
			tels.repayment_amount AS `Repayment Amount`,
			tels.accumulated_repayment_amount AS `Accumulated Amount`,
			CASE
				WHEN tas.name IS NOT NULL AND tas.docstatus = 1 THEN 'Paid'
				ELSE 'Unpaid'
			END AS `Status`,
			tas.name AS `Additional Salary Ref`
		FROM `tabEmployee Loans Schedule` tels
		INNER JOIN `tabEmployee Loans` tel ON tel.name = tels.parent
		LEFT JOIN `tabAdditional Salary` tas ON tas.name = tels.additional_salary_ref
		WHERE tel.docstatus = 1 AND {conditions}
		ORDER BY tel.employee_name, tels.schedule_date
		""",
		filters,
	)


def get_columns():
	return [
		{"label": _("Loan ID"), "fieldname": "Loan ID", "fieldtype": "Link", "options": "Employee Loans", "width": 120},
		{"label": _("Employee ID"), "fieldname": "Employee ID", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "Employee Name", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "Department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Schedule Date"), "fieldname": "Schedule Date", "fieldtype": "Date", "width": 110},
		{"label": _("Repayment Amount"), "fieldname": "Repayment Amount", "fieldtype": "Currency", "options": "currency", "width": 140},
		{"label": _("Accumulated Amount"), "fieldname": "Accumulated Amount", "fieldtype": "Currency", "options": "currency", "width": 150},
		{"label": _("Status"), "fieldname": "Status", "fieldtype": "Data", "width": 90},
		{"label": _("Additional Salary Ref"), "fieldname": "Additional Salary Ref", "fieldtype": "Link", "options": "Additional Salary", "width": 160},
	]
