# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import flt

COMPONENT_TYPES = {"earnings": "Earning", "deductions": "Deduction"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	detail = filters.view == "Employee Detail"
	data = get_data(filters, detail)
	chart, summary = get_chart(data, detail), get_summary(data)
	if data:
		data.append(get_total_row(data))
	return get_columns(detail), data, None, chart, summary


def get_data(filters, detail):
	reposts = get_reposts(filters)
	if not reposts:
		return []

	new_amounts = get_new_amounts([r.name for r in reposts])
	rows = {}
	for repost in reposts:
		original = get_original_amounts(repost.original_data)
		for key in set(original) | set(new_amounts.get(repost.name, {})):
			parentfield, component = key
			if filters.component_type and COMPONENT_TYPES[parentfield] != filters.component_type:
				continue
			old = original.get(key, 0)
			new = new_amounts.get(repost.name, {}).get(key, 0)
			if abs(new - old) < 0.005:
				continue

			group_key = (repost.name, parentfield, component) if detail else (parentfield, component)
			row = rows.setdefault(
				group_key,
				frappe._dict(
					salary_component=component,
					component_type=COMPONENT_TYPES[parentfield],
					original_amount=0,
					new_amount=0,
					reposts=set(),
					employees=set(),
				),
			)
			if detail:
				row.update(
					repost_salary_slip=repost.name,
					status=repost.status,
					payroll_entry=repost.payroll_entry,
					employee=repost.employee,
					employee_name=repost.employee_name,
				)
			row.original_amount += old
			row.new_amount += new
			row.reposts.add(repost.name)
			row.employees.add(repost.employee)

	data = []
	for row in rows.values():
		row.difference = row.new_amount - row.original_amount
		row.change_percent = row.difference / row.original_amount * 100 if row.original_amount else 0
		row.repost_count = len(row.pop("reposts"))
		row.employee_count = len(row.pop("employees"))
		data.append(row)
	return sorted(data, key=lambda r: abs(r.difference), reverse=True)


def get_total_row(data):
	"""Net pay impact of the changes: Earnings difference - Deductions difference."""
	return frappe._dict(
		salary_component=_("Net Pay Impact"),
		bold=1,
		difference=sum(d.difference if d.component_type == "Earning" else -d.difference for d in data),
	)


def get_reposts(filters):
	conditions, values = "", {}
	if filters.status:
		conditions += " and rss.status = %(status)s"
		values["status"] = filters.status
	else:
		conditions += " and rss.docstatus < 2"
	if filters.from_date:
		conditions += " and rss.posting_date >= %(from_date)s"
		values["from_date"] = filters.from_date
	if filters.to_date:
		conditions += " and rss.posting_date <= %(to_date)s"
		values["to_date"] = filters.to_date
	for field in ("company", "payroll_entry", "employee", "department", "project"):
		if filters.get(field):
			conditions += f" and rss.{field} = %({field})s"
			values[field] = filters.get(field)

	return frappe.db.sql(
		f"""
		select rss.name, rss.status, rss.payroll_entry, rss.employee, rss.employee_name, rss.original_data
		from `tabRepost Salary Slip` rss
		where 1 = 1 {conditions}
		""",
		values,
		as_dict=True,
	)


def get_new_amounts(reposts) -> dict:
	"""{repost: {(parentfield, component): amount}} from the repost's Earnings / Deductions"""
	rows = frappe.get_all(
		"Repost Salary Detail",
		filters={"parenttype": "Repost Salary Slip", "parent": ["in", reposts]},
		fields=["parent", "parentfield", "salary_component", "amount"],
	)
	amounts = {}
	for r in rows:
		key = (r.parentfield, r.salary_component)
		repost = amounts.setdefault(r.parent, {})
		repost[key] = repost.get(key, 0) + flt(r.amount)
	return amounts


def get_original_amounts(original_data) -> dict:
	"""{(parentfield, component): amount} from the Salary Slip snapshot taken by the repost, so a
	component removed by the repost still shows as a change."""
	try:
		original = json.loads(original_data or "{}")
	except ValueError:
		return {}
	amounts = {}
	for parentfield in COMPONENT_TYPES:
		for r in original.get(parentfield) or []:
			key = (parentfield, r.get("salary_component"))
			amounts[key] = amounts.get(key, 0) + flt(r.get("amount"))
	return amounts


def get_columns(detail):
	columns = []
	if detail:
		columns += [
			{
				"label": _("Repost Salary Slip"),
				"fieldname": "repost_salary_slip",
				"fieldtype": "Link",
				"options": "Repost Salary Slip",
				"width": 150,
			},
			{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
			{
				"label": _("Payroll Entry"),
				"fieldname": "payroll_entry",
				"fieldtype": "Link",
				"options": "Payroll Entry",
				"width": 160,
			},
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Link",
				"options": "Employee",
				"width": 100,
			},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		]
	columns += [
		{
			"label": _("Salary Component"),
			"fieldname": "salary_component",
			"fieldtype": "Link",
			"options": "Salary Component",
			"width": 200,
		},
		{"label": _("Type"), "fieldname": "component_type", "fieldtype": "Data", "width": 90},
	]
	if not detail:
		columns += [
			{"label": _("Reposts"), "fieldname": "repost_count", "fieldtype": "Int", "width": 80},
			{"label": _("Employees"), "fieldname": "employee_count", "fieldtype": "Int", "width": 90},
		]
	columns += [
		{"label": _("Original Amount"), "fieldname": "original_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("New Amount"), "fieldname": "new_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Difference"), "fieldname": "difference", "fieldtype": "Currency", "width": 140},
		{"label": _("Change %"), "fieldname": "change_percent", "fieldtype": "Percent", "width": 90},
	]
	return columns


def get_chart(data, detail):
	if not data:
		return None

	totals = {}
	for d in data:
		label = f"{d.salary_component} ({_(d.component_type)})"
		totals[label] = totals.get(label, 0) + d.difference
	labels = sorted(totals, key=lambda k: abs(totals[k]), reverse=True)[:15]
	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Difference"), "values": [totals[k] for k in labels]}],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": ["#7575ff"],
	}


def get_summary(data):
	earnings = sum(d.difference for d in data if d.component_type == "Earning")
	deductions = sum(d.difference for d in data if d.component_type == "Deduction")
	return [
		{
			"value": len({d.salary_component for d in data}),
			"label": _("Components Changed"),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{"value": earnings, "label": _("Earnings Difference"), "datatype": "Currency", "indicator": "Green"},
		{"value": deductions, "label": _("Deductions Difference"), "datatype": "Currency", "indicator": "Orange"},
		{
			"value": earnings - deductions,
			"label": _("Net Pay Impact"),
			"datatype": "Currency",
			"indicator": "Green" if earnings - deductions >= 0 else "Red",
		},
	]
