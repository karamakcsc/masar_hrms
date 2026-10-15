# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, formatdate, get_first_day


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_summary(data)


def get_data(filters):
	conditions, values = get_conditions(filters)
	data = frappe.db.sql(
		f"""
		select rss.name as repost_salary_slip, rss.status, rss.posting_date, rss.company,
			rss.payroll_entry, rss.salary_slip, rss.employee, rss.employee_name,
			rss.department, rss.project, rss.start_date, rss.end_date,
			rss.original_gross_pay, rss.gross_pay,
			rss.original_total_deduction, rss.total_deduction,
			rss.original_net_pay, rss.net_pay, rss.net_pay_difference,
			rss.original_income_tax, rss.income_tax,
			rss.employee_social_security, rss.company_social_security,
			rss.repost_payroll, rss.applied_on, rss.applied_by
		from `tabRepost Salary Slip` rss
		where 1 = 1 {conditions}
		order by rss.posting_date desc, rss.name desc
		""",
		values,
		as_dict=True,
	)
	for d in data:
		d.gross_difference = flt(d.gross_pay) - flt(d.original_gross_pay)
		d.deduction_difference = flt(d.total_deduction) - flt(d.original_total_deduction)
		d.income_tax_difference = flt(d.income_tax) - flt(d.original_income_tax)
	return data


def get_conditions(filters):
	conditions, values = "", {}
	if filters.status:
		conditions += " and rss.status = %(status)s"
		values["status"] = filters.status
	elif not filters.include_cancelled:
		conditions += " and rss.docstatus < 2"
	if filters.from_date:
		conditions += " and rss.posting_date >= %(from_date)s"
		values["from_date"] = filters.from_date
	if filters.to_date:
		conditions += " and rss.posting_date <= %(to_date)s"
		values["to_date"] = filters.to_date
	for field in ("company", "payroll_entry", "employee", "department", "project", "repost_payroll"):
		if filters.get(field):
			conditions += f" and rss.{field} = %({field})s"
			values[field] = filters.get(field)
	return conditions, values


def get_columns():
	def currency(label, fieldname, width=130):
		return {"label": _(label), "fieldname": fieldname, "fieldtype": "Currency", "width": width}

	return [
		{
			"label": _("Repost Salary Slip"),
			"fieldname": "repost_salary_slip",
			"fieldtype": "Link",
			"options": "Repost Salary Slip",
			"width": 150,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Payroll Entry"),
			"fieldname": "payroll_entry",
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"width": 160,
		},
		{
			"label": _("Salary Slip"),
			"fieldname": "salary_slip",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 170,
		},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 100},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 140,
		},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
		{"label": _("Period Start"), "fieldname": "start_date", "fieldtype": "Date", "width": 100},
		{"label": _("Period End"), "fieldname": "end_date", "fieldtype": "Date", "width": 100},
		currency("Original Gross", "original_gross_pay"),
		currency("New Gross", "gross_pay"),
		currency("Gross Difference", "gross_difference"),
		currency("Original Deduction", "original_total_deduction"),
		currency("New Deduction", "total_deduction"),
		currency("Deduction Difference", "deduction_difference", 150),
		currency("Original Net Pay", "original_net_pay"),
		currency("New Net Pay", "net_pay"),
		currency("Net Pay Difference", "net_pay_difference", 140),
		currency("Original Income Tax", "original_income_tax", 140),
		currency("New Income Tax", "income_tax"),
		currency("Income Tax Difference", "income_tax_difference", 150),
		currency("Employee Social Security", "employee_social_security", 170),
		currency("Company Social Security", "company_social_security", 170),
		{
			"label": _("Repost Payroll"),
			"fieldname": "repost_payroll",
			"fieldtype": "Link",
			"options": "Repost Payroll",
			"width": 150,
		},
		{"label": _("Applied On"), "fieldname": "applied_on", "fieldtype": "Datetime", "width": 150},
		{"label": _("Applied By"), "fieldname": "applied_by", "fieldtype": "Link", "options": "User", "width": 150},
	]


def get_chart(data):
	"""Net pay difference per payroll month (Payroll period start)."""
	months = {}
	for d in data:
		if d.status == "Cancelled" or not d.start_date:
			continue
		month = get_first_day(d.start_date)
		months[month] = months.get(month, 0) + flt(d.net_pay_difference)
	if not months:
		return None

	labels = sorted(months)
	return {
		"data": {
			"labels": [formatdate(m, "MMM yyyy") for m in labels],
			"datasets": [{"name": _("Net Pay Difference"), "values": [months[m] for m in labels]}],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": ["#ffa00a"],
	}


def get_summary(data):
	active = [d for d in data if d.status != "Cancelled"]

	def count(status):
		return len([d for d in active if d.status == status])

	net_difference = sum(flt(d.net_pay_difference) for d in active)
	return [
		{"value": count("Draft"), "label": _("Draft"), "datatype": "Int", "indicator": "Red"},
		{"value": count("Pending"), "label": _("Pending"), "datatype": "Int", "indicator": "Orange"},
		{"value": count("Applied"), "label": _("Applied"), "datatype": "Int", "indicator": "Green"},
		{
			"value": len({d.employee for d in active}),
			"label": _("Employees"),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"value": net_difference,
			"label": _("Net Pay Difference"),
			"datatype": "Currency",
			"indicator": "Green" if net_difference >= 0 else "Red",
		},
	]
