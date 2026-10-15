# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_first_day, nowdate

from masar_hrms.payroll_budget.report_utils import get_budget_summary, get_period


def _filters(filters):
	filters = frappe.parse_json(filters) if filters else {}
	return frappe._dict(filters if isinstance(filters, dict) else {})


def _currency(value):
	return {"value": value, "fieldtype": "Currency"}


@frappe.whitelist()
def get_total_payroll_budget(filters=None):
	return _currency(get_budget_summary(_filters(filters), to_date=nowdate()).budget)


@frappe.whitelist()
def get_payroll_expensed_to_date(filters=None):
	return _currency(get_budget_summary(_filters(filters), to_date=nowdate()).expensed)


@frappe.whitelist()
def get_payroll_expensed_this_month(filters=None):
	today = nowdate()
	return _currency(get_budget_summary(_filters(filters), get_first_day(today), today).period)


@frappe.whitelist()
def get_payroll_expensed_this_year(filters=None):
	filters = _filters(filters)
	from_date, to_date = get_period(frappe._dict(company=filters.company))
	return _currency(get_budget_summary(filters, from_date, to_date).period)


@frappe.whitelist()
def get_remaining_payroll_budget(filters=None):
	return _currency(get_budget_summary(_filters(filters), to_date=nowdate()).remaining)


@frappe.whitelist()
def get_payroll_budget_utilization(filters=None):
	return {"value": get_budget_summary(_filters(filters), to_date=nowdate()).utilization, "fieldtype": "Percent"}


@frappe.whitelist()
def get_exceeded_payroll_budgets(filters=None):
	return get_budget_summary(_filters(filters), to_date=nowdate()).exceeded


@frappe.whitelist()
def get_employees_without_payroll_budget(filters=None):
	from masar_hrms.payroll_budget.report.employee_payroll_budget_mapping.employee_payroll_budget_mapping import (
		NOT_MAPPED,
		get_employee_mapping,
	)

	return len([e for e in get_employee_mapping(_filters(filters)) if e.mapping_status == NOT_MAPPED])
