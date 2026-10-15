# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	chart, summary = get_chart(data), get_summary(data)
	if data:
		data.append(get_total_row(data))
	return get_columns(), data, None, chart, summary


def get_data(filters):
	conditions, values = get_conditions(filters)
	data = frappe.db.sql(
		f"""
		select rp.name as repost_payroll, rp.status, rp.posting_date, rp.company,
			rp.payroll_entry, rp.payroll_posting_date, rp.start_date, rp.end_date,
			rp.accounting_action, rp.number_of_salary_slips, rp.number_of_reposts,
			rp.employees_affected, rp.old_total_net_pay, rp.new_total_net_pay,
			rp.net_pay_difference, rp.new_journal_entry, rp.completed_on, rp.completed_by
		from `tabRepost Payroll` rp
		where 1 = 1 {conditions}
		order by rp.posting_date desc, rp.name desc
		""",
		values,
		as_dict=True,
	)
	for d in data:
		d.change_percent = (
			flt(d.net_pay_difference) / flt(d.old_total_net_pay) * 100 if flt(d.old_total_net_pay) else 0
		)
		d.affected_ratio = (
			flt(d.employees_affected) / d.number_of_salary_slips * 100 if d.number_of_salary_slips else 0
		)
	return data


def get_total_row(data):
	"""Totals of the non cancelled Repost Payrolls with the ratios recalculated on the totals."""
	rows = [d for d in data if d.status != "Cancelled"]
	total = frappe._dict(repost_payroll=_("Total"), bold=1)
	for field in (
		"number_of_salary_slips",
		"number_of_reposts",
		"employees_affected",
		"old_total_net_pay",
		"new_total_net_pay",
		"net_pay_difference",
	):
		total[field] = sum(flt(d.get(field)) for d in rows)
	total.change_percent = (
		total.net_pay_difference / total.old_total_net_pay * 100 if total.old_total_net_pay else 0
	)
	total.affected_ratio = (
		total.employees_affected / total.number_of_salary_slips * 100 if total.number_of_salary_slips else 0
	)
	return total


def get_conditions(filters):
	conditions, values = "", {}
	if filters.status:
		conditions += " and rp.status = %(status)s"
		values["status"] = filters.status
	elif not filters.include_cancelled:
		conditions += " and rp.docstatus < 2"
	if filters.from_date:
		conditions += " and rp.posting_date >= %(from_date)s"
		values["from_date"] = filters.from_date
	if filters.to_date:
		conditions += " and rp.posting_date <= %(to_date)s"
		values["to_date"] = filters.to_date
	for field in ("company", "payroll_entry", "accounting_action"):
		if filters.get(field):
			conditions += f" and rp.{field} = %({field})s"
			values[field] = filters.get(field)
	return conditions, values


def get_columns():
	return [
		{
			"label": _("Repost Payroll"),
			"fieldname": "repost_payroll",
			"fieldtype": "Link",
			"options": "Repost Payroll",
			"width": 150,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Payroll Entry"),
			"fieldname": "payroll_entry",
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"width": 160,
		},
		{"label": _("Period Start"), "fieldname": "start_date", "fieldtype": "Date", "width": 100},
		{"label": _("Period End"), "fieldname": "end_date", "fieldtype": "Date", "width": 100},
		{"label": _("Accounting Action"), "fieldname": "accounting_action", "fieldtype": "Data", "width": 200},
		{"label": _("Salary Slips"), "fieldname": "number_of_salary_slips", "fieldtype": "Int", "width": 100},
		{"label": _("Reposts"), "fieldname": "number_of_reposts", "fieldtype": "Int", "width": 80},
		{"label": _("Employees Affected"), "fieldname": "employees_affected", "fieldtype": "Int", "width": 130},
		{"label": _("% Slips Affected"), "fieldname": "affected_ratio", "fieldtype": "Percent", "width": 120},
		{"label": _("Original Net Pay"), "fieldname": "old_total_net_pay", "fieldtype": "Currency", "width": 140},
		{"label": _("New Net Pay"), "fieldname": "new_total_net_pay", "fieldtype": "Currency", "width": 140},
		{
			"label": _("Net Pay Difference"),
			"fieldname": "net_pay_difference",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("Change %"), "fieldname": "change_percent", "fieldtype": "Percent", "width": 90},
		{
			"label": _("New Journal Entry"),
			"fieldname": "new_journal_entry",
			"fieldtype": "Link",
			"options": "Journal Entry",
			"width": 150,
		},
		{"label": _("Completed On"), "fieldname": "completed_on", "fieldtype": "Datetime", "width": 150},
		{
			"label": _("Completed By"),
			"fieldname": "completed_by",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
	]


def get_chart(data):
	rows = [d for d in data if d.status == "Completed"][:15][::-1]
	if not rows:
		return None
	return {
		"data": {
			"labels": [d.payroll_entry for d in rows],
			"datasets": [
				{"name": _("Original Net Pay"), "values": [flt(d.old_total_net_pay) for d in rows]},
				{"name": _("New Net Pay"), "values": [flt(d.new_total_net_pay) for d in rows]},
			],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": ["#98d85b", "#5e64ff"],
	}


def get_summary(data):
	completed = [d for d in data if d.status == "Completed"]
	difference = sum(flt(d.net_pay_difference) for d in completed)
	return [
		{"value": len(completed), "label": _("Completed"), "datatype": "Int", "indicator": "Green"},
		{
			"value": len([d for d in data if d.status == "Draft"]),
			"label": _("Draft"),
			"datatype": "Int",
			"indicator": "Red",
		},
		{
			"value": sum(d.number_of_reposts or 0 for d in completed),
			"label": _("Salary Slips Reposted"),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"value": difference,
			"label": _("Net Pay Difference"),
			"datatype": "Currency",
			"indicator": "Green" if difference >= 0 else "Red",
		},
	]
