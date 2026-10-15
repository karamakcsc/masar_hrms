# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, get_first_day, getdate, nowdate


def _year_start():
	return get_first_day(getdate(nowdate()).replace(month=1))


@frappe.whitelist()
def get_employees_affected_this_year(filters=None):
	return frappe.db.sql(
		"""
		select count(distinct employee)
		from `tabRepost Salary Slip`
		where status = 'Applied' and posting_date >= %(year_start)s
		""",
		{"year_start": _year_start()},
	)[0][0]


@frappe.whitelist()
def get_net_pay_difference_this_year(filters=None):
	value = frappe.db.sql(
		"""
		select sum(net_pay_difference)
		from `tabRepost Salary Slip`
		where status = 'Applied' and posting_date >= %(year_start)s
		""",
		{"year_start": _year_start()},
	)[0][0]
	return {"value": flt(value), "fieldtype": "Currency"}
