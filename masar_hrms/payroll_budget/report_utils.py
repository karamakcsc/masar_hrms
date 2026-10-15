# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

"""Shared queries for the Payroll Budget reports, number cards and charts.

Payroll Budget Element = a Budget Element used as Employee Salary Budget or Company Social Security
Budget in any Project Payroll Budget row.
Budget   -> Budget Element.budget_amount
Expensed -> GL Entries booked on the Budget Element against its own account (same rule as the
            Masar Budget "Budget Details" report), cancelled entries excluded.
"""

import frappe
from frappe.utils import flt, getdate, nowdate

from erpnext.accounts.utils import get_fiscal_year

from masar_hrms.payroll_budget.utils import BUDGET_DOCTYPE, BUDGET_ROW_DOCTYPE

SALARY = "Salary"
SOCIAL_SECURITY = "Social Security"
BUDGET_TYPE_FIELDS = {
	SALARY: "employee_salary_budget",
	SOCIAL_SECURITY: "company_social_security_budget",
}


def get_payroll_budget_elements(filters=None) -> list[dict]:
	"""One row per distinct Payroll Budget Element (a Budget Element shared by several dimension rows
	or Projects is returned once, so its budget is never counted twice)."""
	filters = frappe._dict(filters or {})
	budget_types = [filters.budget_type] if filters.budget_type else list(BUDGET_TYPE_FIELDS)

	PPB = frappe.qb.DocType(BUDGET_DOCTYPE)
	Row = frappe.qb.DocType(BUDGET_ROW_DOCTYPE)
	BE = frappe.qb.DocType("Budget Element")

	elements = {}
	for budget_type in budget_types:
		be_field = Row[BUDGET_TYPE_FIELDS[budget_type]]
		query = (
			frappe.qb.from_(Row)
			.join(PPB)
			.on((PPB.name == Row.parent) & (Row.parenttype == BUDGET_DOCTYPE))
			.join(BE)
			.on(BE.name == be_field)
			.select(
				BE.name.as_("budget_element"),
				PPB.project,
				PPB.project_name,
				PPB.company,
				BE.cost_center,
				BE.account_no.as_("account"),
				BE.fiscal_year,
				BE.budget_amount,
			)
			.where(BE.docstatus == 1)
			.orderby(PPB.project)
			.orderby(Row.idx)
		)
		if filters.company:
			query = query.where(PPB.company == filters.company)
		if filters.project:
			query = query.where(PPB.project == filters.project)
		if filters.fiscal_year:
			query = query.where(BE.fiscal_year == filters.fiscal_year)
		if filters.budget_element:
			query = query.where(BE.name == filters.budget_element)

		for row in query.run(as_dict=True):
			if row.budget_element not in elements:
				row.budget_type = budget_type
				row.budget_amount = flt(row.budget_amount)
				elements[row.budget_element] = row

	return list(elements.values())


def get_expense_by_element(elements, from_date=None, to_date=None) -> dict:
	"""{budget_element: {"opening": expensed before from_date, "period": expensed in the period}}"""
	names = [e.budget_element for e in elements]
	if not names:
		return {}

	conditions, values = "", {"names": names, "from_date": from_date}
	if to_date:
		conditions += " and gle.posting_date <= %(to_date)s"
		values["to_date"] = to_date
	opening = "gle.posting_date < %(from_date)s" if from_date else "1 = 0"

	rows = frappe.db.sql(
		f"""
		select gle.budget_element,
			sum(case when {opening} then gle.debit - gle.credit else 0 end) as opening,
			sum(case when {opening} then 0 else gle.debit - gle.credit end) as period
		from `tabGL Entry` gle
		inner join `tabBudget Element` be on be.name = gle.budget_element
		where gle.budget_element in %(names)s
			and gle.is_cancelled = 0
			and gle.account = be.account_no
			{conditions}
		group by gle.budget_element
		""",
		values,
		as_dict=True,
	)
	return {r.budget_element: frappe._dict(opening=flt(r.opening), period=flt(r.period)) for r in rows}


def get_monthly_expense(elements, from_date, to_date) -> list[dict]:
	"""Expensed amount per month and Budget Type between from_date and to_date."""
	budget_types = {e.budget_element: e.budget_type for e in elements}
	if not budget_types:
		return []

	rows = frappe.db.sql(
		"""
		select date_format(gle.posting_date, '%%Y-%%m-01') as month, gle.budget_element,
			sum(gle.debit - gle.credit) as amount
		from `tabGL Entry` gle
		inner join `tabBudget Element` be on be.name = gle.budget_element
		where gle.budget_element in %(names)s
			and gle.is_cancelled = 0
			and gle.account = be.account_no
			and gle.posting_date between %(from_date)s and %(to_date)s
		group by month, gle.budget_element
		order by month
		""",
		{"names": list(budget_types), "from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	for row in rows:
		row.month = getdate(row.month)
		row.budget_type = budget_types[row.budget_element]
		row.amount = flt(row.amount)
	return rows


def get_budget_summary(filters=None, from_date=None, to_date=None) -> frappe._dict:
	"""Totals over every Payroll Budget Element: budget, expensed (opening / period / cumulative)."""
	elements = get_payroll_budget_elements(filters)
	expense = get_expense_by_element(elements, from_date, to_date)

	summary = frappe._dict(budget=0, opening=0, period=0, expensed=0, exceeded=0, elements=len(elements))
	for e in elements:
		spent = expense.get(e.budget_element) or frappe._dict(opening=0, period=0)
		summary.budget += e.budget_amount
		summary.opening += spent.opening
		summary.period += spent.period
		if spent.opening + spent.period > e.budget_amount:
			summary.exceeded += 1
	summary.expensed = summary.opening + summary.period
	summary.remaining = summary.budget - summary.expensed
	summary.utilization = (summary.expensed / summary.budget * 100) if summary.budget else 0
	return summary


def get_utilization_status(budget, expensed) -> str:
	if expensed > budget:
		return "Exceeded"
	if budget and expensed / budget >= 0.9:
		return "Near Limit"
	if not expensed:
		return "Not Used"
	return "Within Budget"


def get_period(filters) -> tuple:
	"""(from_date, to_date) of the filters, defaulting to the current Fiscal Year up to today."""
	filters = frappe._dict(filters or {})
	to_date = getdate(filters.to_date or nowdate())
	from_date = filters.from_date
	if not from_date:
		try:
			from_date = get_fiscal_year(to_date, company=filters.company, verbose=0)[1]
		except Exception:
			from_date = to_date.replace(month=1, day=1)
	return getdate(from_date), to_date
