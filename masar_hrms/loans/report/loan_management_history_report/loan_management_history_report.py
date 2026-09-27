# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _

STATUS_MAP = {"Draft": 0, "Submitted": 1, "Cancelled": 2}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_conditions(filters):
	conditions = " 1=1 "
	if filters.get("employee"):
		conditions += " AND elm.employee = %(employee)s"
	if filters.get("management_type"):
		conditions += " AND elm.management_type = %(management_type)s"
	if filters.get("from_date"):
		conditions += " AND elm.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND elm.posting_date <= %(to_date)s"
	if filters.get("status"):
		filters["docstatus"] = STATUS_MAP.get(filters.get("status"))
		conditions += " AND elm.docstatus = %(docstatus)s"
	return conditions


def get_data(filters):
	conditions = get_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			elm.name AS `Management ID`,
			elm.employee AS `Employee ID`,
			elm.employee_name AS `Employee Name`,
			elm.management_type AS `Management Type`,
			els.emp_loans_ref AS `Loan Ref`,
			els.schedule_date AS `Original Schedule Date`,
			els.new_date AS `New Schedule Date`,
			els.repayment_amount AS `Repayment Amount`,
			els.accumulated_repayment_amount AS `Accumulated Amount`,
			NULL AS `Old Additional Salary Ref`,
			els.additional_salary_ref AS `Additional Salary Ref`,
			CASE elm.docstatus WHEN 0 THEN 'Draft' WHEN 1 THEN 'Submitted' WHEN 2 THEN 'Cancelled' END AS `Status`,
			elm.posting_date AS `Posting Date`
		FROM `tabEmployee Loans Management` elm
		INNER JOIN `tabEmployee Loans Management Schedule` els ON els.parent = elm.name
		WHERE elm.management_type = 'Reschedule' AND {conditions}

		UNION ALL

		SELECT
			elm.name AS `Management ID`,
			elm.employee AS `Employee ID`,
			elm.employee_name AS `Employee Name`,
			elm.management_type AS `Management Type`,
			elt.emp_loans_ref AS `Loan Ref`,
			elt.schedule_date AS `Original Schedule Date`,
			NULL AS `New Schedule Date`,
			elt.repayment_amount AS `Repayment Amount`,
			elt.accumulated_repayment_amount AS `Accumulated Amount`,
			elt.old_add_sal_ref AS `Old Additional Salary Ref`,
			elt.additional_salary_ref AS `Additional Salary Ref`,
			CASE elm.docstatus WHEN 0 THEN 'Draft' WHEN 1 THEN 'Submitted' WHEN 2 THEN 'Cancelled' END AS `Status`,
			elm.posting_date AS `Posting Date`
		FROM `tabEmployee Loans Management` elm
		INNER JOIN `tabEmployee Loans Management Structure` elt ON elt.parent = elm.name
		WHERE elm.management_type = 'Restructure' AND {conditions}

		ORDER BY `Posting Date` DESC
		""",
		filters,
	)


def get_columns():
	return [
		{"label": _("Management ID"), "fieldname": "Management ID", "fieldtype": "Link", "options": "Employee Loans Management", "width": 140},
		{"label": _("Employee ID"), "fieldname": "Employee ID", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "Employee Name", "fieldtype": "Data", "width": 150},
		{"label": _("Management Type"), "fieldname": "Management Type", "fieldtype": "Data", "width": 110},
		{"label": _("Loan Ref"), "fieldname": "Loan Ref", "fieldtype": "Link", "options": "Employee Loans", "width": 130},
		{"label": _("Original Schedule Date"), "fieldname": "Original Schedule Date", "fieldtype": "Date", "width": 150},
		{"label": _("New Schedule Date"), "fieldname": "New Schedule Date", "fieldtype": "Date", "width": 140},
		{"label": _("Repayment Amount"), "fieldname": "Repayment Amount", "fieldtype": "Currency", "options": "currency", "width": 140},
		{"label": _("Accumulated Amount"), "fieldname": "Accumulated Amount", "fieldtype": "Currency", "options": "currency", "width": 150},
		{"label": _("Old Additional Salary Ref"), "fieldname": "Old Additional Salary Ref", "fieldtype": "Link", "options": "Additional Salary", "width": 170},
		{"label": _("Additional Salary Ref"), "fieldname": "Additional Salary Ref", "fieldtype": "Link", "options": "Additional Salary", "width": 160},
		{"label": _("Status"), "fieldname": "Status", "fieldtype": "Data", "width": 90},
		{"label": _("Posting Date"), "fieldname": "Posting Date", "fieldtype": "Date", "width": 110},
	]
