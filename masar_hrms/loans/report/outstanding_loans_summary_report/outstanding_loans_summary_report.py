# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_conditions(filters):
	conditions = " 1=1 "
	if filters.get("company"):
		conditions += " AND tel.company = %(company)s"
	if filters.get("department"):
		conditions += " AND tel.department = %(department)s"
	return conditions


def get_data(filters):
	conditions = get_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			per_loan.department AS `Department`,
			per_loan.company AS `Company`,
			COUNT(*) AS `Number of Loans`,
			SUM(per_loan.loan_amount) AS `Total Loan Amount`,
			SUM(per_loan.repaid) AS `Total Repaid`,
			SUM(per_loan.loan_amount - per_loan.repaid) AS `Total Outstanding`
		FROM (
			SELECT
				tel.name, tel.department, tel.company, tel.loan_amount,
				IFNULL(SUM(tas.amount), 0) AS repaid
			FROM `tabEmployee Loans` tel
			LEFT JOIN `tabEmployee Loans Schedule` tels ON tels.parent = tel.name
			LEFT JOIN `tabAdditional Salary` tas ON tas.name = tels.additional_salary_ref
				AND tas.docstatus = 1
				AND tas.salary_component = 'Loan'
				AND tas.payroll_date <= CURDATE()
			WHERE tel.docstatus = 1 AND {conditions}
			GROUP BY tel.name
		) per_loan
		GROUP BY per_loan.department, per_loan.company
		ORDER BY `Total Outstanding` DESC
		""",
		filters,
	)


def get_columns():
	return [
		{"label": _("Department"), "fieldname": "Department", "fieldtype": "Link", "options": "Department", "width": 180},
		{"label": _("Company"), "fieldname": "Company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"label": _("Number of Loans"), "fieldname": "Number of Loans", "fieldtype": "Int", "width": 120},
		{"label": _("Total Loan Amount"), "fieldname": "Total Loan Amount", "fieldtype": "Currency", "options": "currency", "width": 150},
		{"label": _("Total Repaid"), "fieldname": "Total Repaid", "fieldtype": "Currency", "options": "currency", "width": 140},
		{"label": _("Total Outstanding"), "fieldname": "Total Outstanding", "fieldtype": "Currency", "options": "currency", "width": 150},
	]
