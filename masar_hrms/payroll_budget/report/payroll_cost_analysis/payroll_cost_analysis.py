# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate

from masar_hrms.payroll_budget.report_utils import get_period

# Group By option -> (Salary Slip expression, column fieldtype, Link options)
GROUP_BY = {
	"Project": ("ss.custom_project", "Link", "Project"),
	"Department": ("ss.department", "Link", "Department"),
	"Designation": ("ss.designation", "Link", "Designation"),
	"Branch": ("ss.branch", "Link", "Branch"),
	"Salary Budget Element": ("ss.custom_salary_budget_element", "Link", "Budget Element"),
	"Salary Cost Center": ("ss.custom_salary_cost_center", "Link", "Cost Center"),
	"Social Security Budget Element": ("ss.custom_ss_budget_element", "Link", "Budget Element"),
	"Payroll Entry": ("ss.payroll_entry", "Link", "Payroll Entry"),
	"Month": ("date_format(ss.start_date, '%%Y-%%m-01')", "Data", None),
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	filters.group_by = filters.group_by if filters.group_by in GROUP_BY else "Project"

	data = get_data(filters)
	chart, summary = get_chart(data, filters), get_summary(data)
	if data:
		data.append(get_total_row(filters, data))
	return get_columns(filters), data, None, chart, summary


def get_data(filters):
	from_date, to_date = get_period(filters)
	group_expr = GROUP_BY[filters.group_by][0]
	conditions, values = get_conditions(filters)
	values.update(from_date=from_date, to_date=to_date)

	rows = frappe.db.sql(
		f"""
		select {group_expr} as group_value,
			count(distinct ss.employee) as employees,
			count(ss.name) as salary_slips,
			sum(ss.base_gross_pay) as gross_pay,
			sum(ss.base_total_deduction) as total_deduction,
			sum(ss.base_net_pay) as net_pay,
			sum(ss.payment_days) as payment_days
		from `tabSalary Slip` ss
		where ss.docstatus = 1
			and ss.start_date between %(from_date)s and %(to_date)s
			{conditions}
		group by group_value
		order by {"group_value" if filters.group_by == "Month" else "gross_pay desc"}
		""",
		values,
		as_dict=True,
	)

	total_gross = sum(flt(r.gross_pay) for r in rows)
	for r in rows:
		if filters.group_by == "Month" and r.group_value:
			r.group_value = formatdate(getdate(r.group_value), "MMM yyyy")
		r.group_value = r.group_value or _("Not Set")
		r.avg_gross_per_employee = flt(r.gross_pay) / r.employees if r.employees else 0
		r.gross_share = flt(r.gross_pay) / total_gross * 100 if total_gross else 0
	return rows


def get_total_row(filters, data):
	"""Totals with distinct Employees across groups and the average recalculated on the totals."""
	from_date, to_date = get_period(filters)
	conditions, values = get_conditions(filters)
	values.update(from_date=from_date, to_date=to_date)
	employees = frappe.db.sql(
		f"""
		select count(distinct ss.employee)
		from `tabSalary Slip` ss
		where ss.docstatus = 1
			and ss.start_date between %(from_date)s and %(to_date)s
			{conditions}
		""",
		values,
	)[0][0]

	gross = sum(flt(r.gross_pay) for r in data)
	return frappe._dict(
		group_value=_("Total"),
		bold=1,
		employees=employees,
		salary_slips=sum(r.salary_slips for r in data),
		payment_days=sum(flt(r.payment_days) for r in data),
		gross_pay=gross,
		total_deduction=sum(flt(r.total_deduction) for r in data),
		net_pay=sum(flt(r.net_pay) for r in data),
		avg_gross_per_employee=gross / employees if employees else 0,
		gross_share=100 if gross else 0,
	)


def get_conditions(filters):
	conditions, values = "", {}
	for field, column in (
		("company", "ss.company"),
		("project", "ss.custom_project"),
		("department", "ss.department"),
		("branch", "ss.branch"),
		("payroll_entry", "ss.payroll_entry"),
		("employee", "ss.employee"),
	):
		if filters.get(field):
			conditions += f" and {column} = %({field})s"
			values[field] = filters.get(field)
	return conditions, values


def get_columns(filters):
	_expr, fieldtype, options = GROUP_BY[filters.group_by]
	return [
		{
			"label": _(filters.group_by),
			"fieldname": "group_value",
			"fieldtype": fieldtype,
			"options": options,
			"width": 240,
		},
		{"label": _("Employees"), "fieldname": "employees", "fieldtype": "Int", "width": 100},
		{"label": _("Salary Slips"), "fieldname": "salary_slips", "fieldtype": "Int", "width": 100},
		{"label": _("Payment Days"), "fieldname": "payment_days", "fieldtype": "Float", "width": 110},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 150},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 150},
		{
			"label": _("Avg Gross / Employee"),
			"fieldname": "avg_gross_per_employee",
			"fieldtype": "Currency",
			"width": 150,
		},
		{"label": _("% of Gross"), "fieldname": "gross_share", "fieldtype": "Percent", "width": 100},
	]


def get_chart(data, filters):
	if not data:
		return None
	rows = data if filters.group_by == "Month" else data[:15]
	return {
		"data": {
			"labels": [r.group_value for r in rows],
			"datasets": [
				{"name": _("Gross Pay"), "values": [flt(r.gross_pay) for r in rows]},
				{"name": _("Net Pay"), "values": [flt(r.net_pay) for r in rows]},
			],
		},
		"type": "line" if filters.group_by == "Month" else "bar",
		"fieldtype": "Currency",
		"colors": ["#5e64ff", "#28a745"],
	}


def get_summary(data):
	gross = sum(flt(r.gross_pay) for r in data)
	deduction = sum(flt(r.total_deduction) for r in data)
	net = sum(flt(r.net_pay) for r in data)
	slips = sum(r.salary_slips for r in data)
	return [
		{"value": slips, "label": _("Salary Slips"), "datatype": "Int", "indicator": "Blue"},
		{"value": gross, "label": _("Gross Pay"), "datatype": "Currency", "indicator": "Blue"},
		{"value": deduction, "label": _("Total Deduction"), "datatype": "Currency", "indicator": "Orange"},
		{"value": net, "label": _("Net Pay"), "datatype": "Currency", "indicator": "Green"},
	]
