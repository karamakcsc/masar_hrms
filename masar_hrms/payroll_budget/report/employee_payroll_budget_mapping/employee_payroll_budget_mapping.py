# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import strip_html

from masar_hrms.payroll_budget.utils import (
	EMPLOYEE_PROJECT_FIELD,
	PAYROLL_DIMENSIONS,
	_match_employee_budget,
	get_budget_rows_by_project,
	get_dimension_settings,
)

MAPPED = "Mapped"
NOT_MAPPED = "Not Mapped"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_summary(data)


def get_employee_mapping(filters=None) -> list[dict]:
	"""Every employee with the Payroll Budget row it resolves to, or the reason it does not."""
	filters = frappe._dict(filters or {})
	emp_filters = {"status": filters.status or "Active"}
	for field in ("company", "department", "branch"):
		if filters.get(field):
			emp_filters[field] = filters.get(field)
	if filters.project:
		emp_filters[EMPLOYEE_PROJECT_FIELD] = filters.project

	fields = ["name", "employee_name", "company", EMPLOYEE_PROJECT_FIELD] + [
		d["employee_field"] for d in PAYROLL_DIMENSIONS.values()
	]
	employees = frappe.get_all("Employee", filters=emp_filters, fields=fields, order_by="name")

	dimension_settings = get_dimension_settings()
	budget_rows = get_budget_rows_by_project(e.get(EMPLOYEE_PROJECT_FIELD) for e in employees)

	for emp in employees:
		budget, error = _match_employee_budget(emp, dimension_settings, budget_rows)
		budget = budget or frappe._dict()
		dimensions = dimension_settings.get(emp.get(EMPLOYEE_PROJECT_FIELD))
		emp.update(
			employee=emp.name,
			project=emp.get(EMPLOYEE_PROJECT_FIELD),
			section=emp.get(PAYROLL_DIMENSIONS["Section"]["employee_field"]),
			enabled_dimensions=", ".join(dimensions) if dimensions else "",
			salary_budget_element=budget.salary_budget_element,
			salary_cost_center=budget.salary_cost_center,
			ss_budget_element=budget.ss_budget_element,
			ss_cost_center=budget.ss_cost_center,
			mapping_status=NOT_MAPPED if error else MAPPED,
			issue=strip_html(error) if error else "",
		)
	return employees


def get_data(filters):
	data = get_employee_mapping(filters)
	if filters.only_not_mapped:
		data = [d for d in data if d.mapping_status == NOT_MAPPED]
	return data


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 110},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "mapping_status", "fieldtype": "Data", "width": 110},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 110},
		{"label": _("Enabled Dimensions"), "fieldname": "enabled_dimensions", "fieldtype": "Data", "width": 160},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 130,
		},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link", "options": "Employee Grade", "width": 100},
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 100},
		{"label": _("Work Type"), "fieldname": "work_type", "fieldtype": "Data", "width": 90},
		{
			"label": _("Salary Budget Element"),
			"fieldname": "salary_budget_element",
			"fieldtype": "Link",
			"options": "Budget Element",
			"width": 240,
		},
		{
			"label": _("Salary Cost Center"),
			"fieldname": "salary_cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"label": _("Social Security Budget Element"),
			"fieldname": "ss_budget_element",
			"fieldtype": "Link",
			"options": "Budget Element",
			"width": 240,
		},
		{
			"label": _("Social Security Cost Center"),
			"fieldname": "ss_cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{"label": _("Issue"), "fieldname": "issue", "fieldtype": "Data", "width": 400},
	]


def get_chart(data):
	if not data:
		return None
	mapped = len([d for d in data if d.mapping_status == MAPPED])
	return {
		"data": {
			"labels": [_(MAPPED), _(NOT_MAPPED)],
			"datasets": [{"name": _("Employees"), "values": [mapped, len(data) - mapped]}],
		},
		"type": "donut",
		"colors": ["#28a745", "#ff5858"],
	}


def get_summary(data):
	mapped = len([d for d in data if d.mapping_status == MAPPED])
	not_mapped = len(data) - mapped
	return [
		{"value": len(data), "label": _("Employees"), "datatype": "Int", "indicator": "Blue"},
		{"value": mapped, "label": _(MAPPED), "datatype": "Int", "indicator": "Green"},
		{"value": not_mapped, "label": _(NOT_MAPPED), "datatype": "Int", "indicator": "Red" if not_mapped else "Green"},
	]
