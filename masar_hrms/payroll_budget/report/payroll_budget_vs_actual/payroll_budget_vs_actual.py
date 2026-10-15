# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from masar_hrms.payroll_budget.report_utils import (
	get_expense_by_element,
	get_payroll_budget_elements,
	get_period,
	get_utilization_status,
)

def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date, to_date = get_period(filters)

	data = get_data(filters, from_date, to_date)
	if filters.group_by == "Project":
		data = group_by_project(data)
	if filters.only_exceeded:
		data = [d for d in data if d.status == "Exceeded"]

	chart, summary = get_chart(data, filters), get_summary(data)
	if data:
		data.append(get_total_row(data))
	return get_columns(filters), data, None, chart, summary


def get_data(filters, from_date, to_date):
	elements = get_payroll_budget_elements(filters)
	expense = get_expense_by_element(elements, from_date, to_date)

	data = []
	for e in elements:
		spent = expense.get(e.budget_element) or frappe._dict(opening=0, period=0)
		data.append(make_row(e, e.budget_amount, spent.opening, spent.period))
	return data


def make_row(row, budget, opening, period):
	row.budget_amount = flt(budget)
	row.opening_expense = flt(opening)
	row.period_expense = flt(period)
	row.cumulative_expense = row.opening_expense + row.period_expense
	row.remaining_budget = row.budget_amount - row.cumulative_expense
	row.utilization = (row.cumulative_expense / row.budget_amount * 100) if row.budget_amount else 0
	row.status = get_utilization_status(row.budget_amount, row.cumulative_expense)
	return row


def group_by_project(data):
	projects = {}
	for d in data:
		p = projects.setdefault(
			d.project,
			frappe._dict(
				project=d.project, project_name=d.project_name, company=d.company, budget=0, opening=0, period=0
			),
		)
		p.budget += d.budget_amount
		p.opening += d.opening_expense
		p.period += d.period_expense
	return [make_row(p, p.budget, p.opening, p.period) for p in projects.values()]


def get_total_row(data):
	"""Totals with Utilization recalculated on the totals (the standard total row would average it)."""
	row = make_row(
		frappe._dict(project_name=_("Total"), bold=1),
		sum(d.budget_amount for d in data),
		sum(d.opening_expense for d in data),
		sum(d.period_expense for d in data),
	)
	row.status = None
	return row


def get_columns(filters):
	columns = [
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 120},
		{"label": _("Project Name"), "fieldname": "project_name", "fieldtype": "Data", "width": 180},
	]
	if filters.group_by != "Project":
		columns += [
			{"label": _("Budget Type"), "fieldname": "budget_type", "fieldtype": "Data", "width": 120},
			{
				"label": _("Budget Element"),
				"fieldname": "budget_element",
				"fieldtype": "Link",
				"options": "Budget Element",
				"width": 260,
			},
			{
				"label": _("Cost Center"),
				"fieldname": "cost_center",
				"fieldtype": "Link",
				"options": "Cost Center",
				"width": 160,
			},
			{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 200},
			{
				"label": _("Fiscal Year"),
				"fieldname": "fiscal_year",
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"width": 90,
			},
		]
	columns += [
		{"label": _("Budget Amount"), "fieldname": "budget_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Expensed Before Period"), "fieldname": "opening_expense", "fieldtype": "Currency", "width": 150},
		{"label": _("Expensed In Period"), "fieldname": "period_expense", "fieldtype": "Currency", "width": 140},
		{"label": _("Cumulative Expensed"), "fieldname": "cumulative_expense", "fieldtype": "Currency", "width": 150},
		{"label": _("Remaining Budget"), "fieldname": "remaining_budget", "fieldtype": "Currency", "width": 140},
		{"label": _("Utilization %"), "fieldname": "utilization", "fieldtype": "Percent", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]
	return columns


def get_chart(data, filters):
	if not data:
		return None

	label_field = "project" if filters.group_by == "Project" else "budget_element"
	rows = sorted(data, key=lambda d: d.budget_amount, reverse=True)[:15]
	return {
		"data": {
			"labels": [d.get(label_field) for d in rows],
			"datasets": [
				{"name": _("Budget"), "values": [d.budget_amount for d in rows]},
				{"name": _("Cumulative Expensed"), "values": [d.cumulative_expense for d in rows]},
				{"name": _("Remaining"), "values": [max(d.remaining_budget, 0) for d in rows]},
			],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": ["#5e64ff", "#ff5858", "#28a745"],
	}


def get_summary(data):
	budget = sum(d.budget_amount for d in data)
	period = sum(d.period_expense for d in data)
	cumulative = sum(d.cumulative_expense for d in data)
	remaining = budget - cumulative
	exceeded = len([d for d in data if d.status == "Exceeded"])
	return [
		{"value": budget, "label": _("Total Budget"), "datatype": "Currency", "indicator": "Blue"},
		{"value": period, "label": _("Expensed In Period"), "datatype": "Currency", "indicator": "Orange"},
		{"value": cumulative, "label": _("Cumulative Expensed"), "datatype": "Currency", "indicator": "Orange"},
		{
			"value": remaining,
			"label": _("Remaining Budget"),
			"datatype": "Currency",
			"indicator": "Green" if remaining >= 0 else "Red",
		},
		{
			"value": (cumulative / budget * 100) if budget else 0,
			"label": _("Utilization %"),
			"datatype": "Percent",
			"indicator": "Blue",
		},
		{"value": exceeded, "label": _("Exceeded"), "datatype": "Int", "indicator": "Red" if exceeded else "Green"},
	]
