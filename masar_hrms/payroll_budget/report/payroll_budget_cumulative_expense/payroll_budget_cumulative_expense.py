# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, flt, formatdate, get_first_day

from masar_hrms.payroll_budget.report_utils import (
	SALARY,
	SOCIAL_SECURITY,
	get_expense_by_element,
	get_monthly_expense,
	get_payroll_budget_elements,
	get_period,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date, to_date = get_period(filters)
	if from_date > to_date:
		frappe.throw(_("From Date cannot be after To Date."))

	elements = get_payroll_budget_elements(filters)
	budget = sum(e.budget_amount for e in elements)
	data = get_data(elements, budget, from_date, to_date)

	return get_columns(), data, None, get_chart(data, budget), get_summary(data, budget)


def get_data(elements, budget, from_date, to_date):
	budget_types = {e.budget_element: e.budget_type for e in elements}

	# expensed before the period, split by Budget Type
	opening = {SALARY: 0, SOCIAL_SECURITY: 0}
	for be, spent in get_expense_by_element(elements, from_date, to_date).items():
		opening[budget_types[be]] += spent.opening

	monthly = {}
	for row in get_monthly_expense(elements, from_date, to_date):
		month = monthly.setdefault(row.month, {SALARY: 0, SOCIAL_SECURITY: 0})
		month[row.budget_type] += row.amount

	data = []
	cumulative = dict(opening)
	if opening[SALARY] or opening[SOCIAL_SECURITY]:
		data.append(make_row(_("Opening (before {0})").format(formatdate(from_date)), None, opening, cumulative, budget))

	month = get_first_day(from_date)
	while month <= to_date:
		amounts = monthly.get(month) or {SALARY: 0, SOCIAL_SECURITY: 0}
		cumulative = {t: cumulative[t] + amounts[t] for t in cumulative}
		data.append(make_row(formatdate(month, "MMM yyyy"), month, amounts, cumulative, budget))
		month = add_months(month, 1)

	return data


def make_row(label, month, amounts, cumulative, budget):
	total = amounts[SALARY] + amounts[SOCIAL_SECURITY]
	cumulative_total = cumulative[SALARY] + cumulative[SOCIAL_SECURITY]
	return frappe._dict(
		period=label,
		month=month,
		salary_expense=flt(amounts[SALARY]),
		ss_expense=flt(amounts[SOCIAL_SECURITY]),
		total_expense=flt(total),
		cumulative_salary=flt(cumulative[SALARY]),
		cumulative_ss=flt(cumulative[SOCIAL_SECURITY]),
		cumulative_total=flt(cumulative_total),
		budget_amount=flt(budget),
		remaining_budget=flt(budget - cumulative_total),
		period_utilization=(total / budget * 100) if budget else 0,
		cumulative_utilization=(cumulative_total / budget * 100) if budget else 0,
	)


def get_columns():
	return [
		{"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 160},
		{"label": _("Salary Expense"), "fieldname": "salary_expense", "fieldtype": "Currency", "width": 140},
		{"label": _("Social Security Expense"), "fieldname": "ss_expense", "fieldtype": "Currency", "width": 160},
		{"label": _("Total Expense"), "fieldname": "total_expense", "fieldtype": "Currency", "width": 140},
		{"label": _("Cumulative Salary"), "fieldname": "cumulative_salary", "fieldtype": "Currency", "width": 150},
		{
			"label": _("Cumulative Social Security"),
			"fieldname": "cumulative_ss",
			"fieldtype": "Currency",
			"width": 180,
		},
		{"label": _("Cumulative Total"), "fieldname": "cumulative_total", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Budget"), "fieldname": "budget_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Remaining Budget"), "fieldname": "remaining_budget", "fieldtype": "Currency", "width": 140},
		{"label": _("Period % of Budget"), "fieldname": "period_utilization", "fieldtype": "Percent", "width": 130},
		{
			"label": _("Cumulative % of Budget"),
			"fieldname": "cumulative_utilization",
			"fieldtype": "Percent",
			"width": 160,
		},
	]


def get_chart(data, budget):
	rows = [d for d in data if d.month]
	if not rows:
		return None
	return {
		"data": {
			"labels": [d.period for d in rows],
			"datasets": [
				{"name": _("Monthly Expense"), "values": [d.total_expense for d in rows]},
				{"name": _("Cumulative Expense"), "values": [d.cumulative_total for d in rows]},
				{"name": _("Budget"), "values": [flt(budget)] * len(rows)},
			],
		},
		"type": "line",
		"fieldtype": "Currency",
		"colors": ["#ffa00a", "#ff5858", "#5e64ff"],
		"lineOptions": {"regionFill": 0, "dotSize": 4},
	}


def get_summary(data, budget):
	period_total = sum(d.total_expense for d in data if d.month)
	cumulative = data[-1].cumulative_total if data else 0
	months = len([d for d in data if d.month and d.total_expense]) or 1
	return [
		{"value": budget, "label": _("Total Budget"), "datatype": "Currency", "indicator": "Blue"},
		{"value": period_total, "label": _("Expensed In Period"), "datatype": "Currency", "indicator": "Orange"},
		{"value": cumulative, "label": _("Cumulative Expensed"), "datatype": "Currency", "indicator": "Orange"},
		{
			"value": budget - cumulative,
			"label": _("Remaining Budget"),
			"datatype": "Currency",
			"indicator": "Green" if budget >= cumulative else "Red",
		},
		{
			"value": period_total / months,
			"label": _("Average Monthly Expense"),
			"datatype": "Currency",
			"indicator": "Blue",
		},
	]
