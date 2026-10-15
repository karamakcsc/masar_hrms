# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

"""Shared logic for Repost Salary Slip and Repost Payroll.

Repost Salary Slip  -> prepares the new state of one submitted Salary Slip as JSON (no accounting)
Repost Payroll      -> applies every prepared repost of a Payroll Entry, recalculates the cumulative
                       (YTD / MTD) values and creates ONE consolidated accrual Journal Entry
"""

import hashlib
import json

import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, get_first_day, getdate, now_datetime

from erpnext.accounts.general_ledger import (
	check_freezing_date,
	validate_accounting_period,
	validate_against_pcv,
)
from erpnext.accounts.utils import get_fiscal_year

from masar_hrms.override._salary_slip import get_salary_component_data
from masar_hrms.payroll_budget.utils import (
	EMPLOYEE_PROJECT_FIELD,
	PAYROLL_DIMENSIONS,
	get_project_dimensions,
	is_payroll_budget_enabled,
	resolve_payroll_budget,
)

REPOST_JSON_VERSION = 1

# Repost dimension field -> Employee field (the input of the Payroll budget resolver)
DIMENSION_FIELDS = {
	"project": EMPLOYEE_PROJECT_FIELD,
	**{label.lower().replace(" ", "_"): d["employee_field"] for label, d in PAYROLL_DIMENSIONS.items()},
}
# Payroll Budget Settings label -> repost dimension field
DIMENSION_LABEL_FIELD = {label: label.lower().replace(" ", "_") for label in PAYROLL_DIMENSIONS}
# Repost dimension field -> Salary Slip field (grade / section are not stored on the slip)
SLIP_DIMENSION_FIELDS = {
	"project": "custom_project",
	"department": "department",
	"designation": "designation",
	"branch": "branch",
	"work_type": "work_type",
}
# Repost budget field -> Salary Slip field
SLIP_BUDGET_FIELDS = {
	"salary_budget_element": "custom_salary_budget_element",
	"salary_cost_center": "custom_salary_cost_center",
	"salary_project": "custom_salary_project",
	"ss_budget_element": "custom_ss_budget_element",
	"ss_cost_center": "custom_ss_cost_center",
	"ss_project": "custom_ss_project",
}
# Salary Detail fields copied between the slip, the repost and the JSON
DETAIL_FIELDS = (
	"salary_component",
	"abbr",
	"amount",
	"default_amount",
	"additional_amount",
	"additional_salary",
	"is_recurring_additional_salary",
	"statistical_component",
	"depends_on_payment_days",
	"exempted_from_income_tax",
	"is_tax_applicable",
	"is_flexible_benefit",
	"variable_based_on_taxable_salary",
	"do_not_include_in_total",
	"do_not_include_in_accounts",
	"deduct_full_tax_on_selected_payroll_date",
	"condition",
	"amount_based_on_formula",
	"formula",
	"tax_on_flexible_benefit",
	"tax_on_additional_salary",
)
COMPONENT_FLAG_FIELDS = (
	"abbr",
	"depends_on_payment_days",
	"do_not_include_in_total",
	"is_tax_applicable",
	"is_flexible_benefit",
	"variable_based_on_taxable_salary",
)
# Salary Slip income tax breakup (Salary Slip.compute_income_tax_breakup)
TAX_BREAKUP_FIELDS = (
	"ctc",
	"income_from_other_sources",
	"total_earnings",
	"non_taxable_earnings",
	"standard_tax_exemption_amount",
	"tax_exemption_declaration",
	"deductions_before_tax_calculation",
	"annual_taxable_amount",
	"income_tax_deducted_till_date",
	"current_month_income_tax",
	"future_income_tax_deductions",
	"total_income_tax",
)
# Employee Social Security is the deduction whose formula is this Employee field
SS_FORMULA = "social_security_amount"
# Social Security (employee and company share) applies only above this number of payment days
SS_MIN_PAYMENT_DAYS = 15

ACTION_REVERSE = "Reverse Existing Journal Entry"
ACTION_CANCEL = "Cancel Existing Journal Entry"


# ---------------------------------------------------------------- permissions


def check_repost_permissions(payroll_entry, salary_slip=None, accounting_action=None):
	"""Reposting is allowed only to users who may run the corresponding Payroll operation:
	write on the Payroll Entry (as Payroll's accrual), write on the Salary Slip, read on the
	Payroll Budget configuration and, when applying, the Journal Entry rights of the action."""
	checks = [("Payroll Entry", "write", payroll_entry)]
	if salary_slip:
		checks.append(("Salary Slip", "write", salary_slip))
	if is_payroll_budget_enabled():
		checks += [("Payroll Budget Settings", "read", None), ("Project Payroll Budget", "read", None)]
	if accounting_action:
		checks += [("Journal Entry", "create", None), ("Journal Entry", "submit", None)]
		if accounting_action == ACTION_CANCEL:
			checks.append(("Journal Entry", "cancel", None))

	for doctype, ptype, name in checks:
		if not frappe.has_permission(doctype, ptype, doc=name):
			frappe.throw(
				_("Not permitted: {0} permission on {1} {2} is required to repost.").format(
					frappe.bold(_(ptype).title()), _(doctype), frappe.bold(name or "")
				),
				frappe.PermissionError,
			)


# ---------------------------------------------------------------- accounting period


def validate_accounting_date(company, posting_date, label=None, voucher_type="Journal Entry"):
	"""Same checks ERPNext runs when GL Entries are made: open Fiscal Year, closed Accounting Period,
	Accounts Frozen Till date and Period Closing Voucher."""
	label = label or _("Posting Date")
	get_fiscal_year(posting_date, company=company, label=label)
	validate_accounting_period(
		[frappe._dict(posting_date=posting_date, company=company, voucher_type=voucher_type)]
	)
	check_freezing_date(posting_date)
	validate_against_pcv(False, posting_date, company)


# ---------------------------------------------------------------- social security


def get_social_security_component(salary_structure):
	"""Deduction component computing the Employee Social Security (formula `social_security_amount`)."""
	cache_key = ("repost_ss_component", salary_structure)
	if cache_key in frappe.local.cache:
		return frappe.local.cache[cache_key]

	component = None
	if salary_structure:
		rows = frappe.get_all(
			"Salary Detail",
			filters={"parenttype": "Salary Structure", "parent": salary_structure, "parentfield": "deductions"},
			fields=["salary_component", "formula"],
		)
		component = next(
			(r.salary_component for r in rows if (r.formula or "").strip() == SS_FORMULA), None
		)
	if not component:
		rows = frappe.get_all(
			"Salary Component", filters={"type": "Deduction", "disabled": 0}, fields=["name", "formula"]
		)
		component = next((r.name for r in rows if (r.formula or "").strip() == SS_FORMULA), None)

	frappe.local.cache[cache_key] = component
	return component


def get_original_social_security(slip):
	"""Social Security input used by the slip's current accounting: the repost snapshot when the slip
	was already reposted, else the Employee values (as read by Payroll's accrual Journal Entry)."""
	if cint(slip.get("custom_ss_snapshot")):
		return frappe._dict(
			applicable=cint(slip.custom_ss_applicable),
			salary=flt(slip.custom_ss_base_salary),
			hazard=cint(slip.custom_ss_hazard),
		)
	emp = frappe.db.get_value(
		"Employee",
		slip.employee,
		["is_social_security_applicable", "social_security_salary", "custom_is_hazard"],
		as_dict=True,
	)
	return frappe._dict(
		applicable=cint(emp.is_social_security_applicable),
		salary=flt(emp.social_security_salary),
		hazard=cint(emp.custom_is_hazard),
	)


def calculate_social_security(company, employee, payment_days, applicable, salary, hazard):
	"""Employee / Company share with the rates of Employee Social Security Salary:
	employee rate = Employee rate or Company default, company rate = normal or dangerous (hazard)."""
	company_rates = frappe.get_cached_value(
		"Company",
		company,
		["employee_share_rate", "company_share_rate", "custom_company_share_rate_dangerous"],
		as_dict=True,
	)
	employee_rate = flt(frappe.db.get_value("Employee", employee, "employee_share_rate")) or flt(
		company_rates.employee_share_rate
	)
	company_rate = flt(
		company_rates.custom_company_share_rate_dangerous if hazard else company_rates.company_share_rate
	)
	eligible = bool(cint(applicable) and flt(payment_days) > SS_MIN_PAYMENT_DAYS)
	return frappe._dict(
		eligible=eligible,
		employee_rate=employee_rate,
		company_rate=company_rate,
		employee_amount=flt(salary) * employee_rate / 100 if eligible else 0,
		company_amount=flt(salary) * company_rate / 100 if eligible else 0,
	)


# ---------------------------------------------------------------- income tax


def is_tax_row(row):
	"""Income Tax rows are calculated by the Salary Slip tax logic, like Salary Slip.add_tax_components."""
	return bool(cint(row.get("variable_based_on_taxable_salary")))


def sync_row_amounts(row, payment_days, working_days):
	"""An edited amount is the final (payment days based) amount. The Salary Slip tax logic reads
	default / additional amount and prorates them by payment days, so set them to give that amount back."""
	factor = 1
	if cint(row.get("depends_on_payment_days")) and flt(working_days) and flt(payment_days):
		factor = flt(working_days) / flt(payment_days)
	if row.get("additional_salary"):
		row.default_amount = 0
		row.additional_amount = flt(row.amount) * factor
	else:
		row.default_amount = flt(row.amount) * factor
		row.additional_amount = 0


def prepare_tax_context(slip):
	"""State Salary Slip.calculate_net_pay builds before the tax components are calculated."""
	from hrms.payroll.doctype.payroll_period.payroll_period import get_period_factor

	slip._salary_structure_doc = frappe.get_cached_doc("Salary Structure", slip.salary_structure)
	slip.set_salary_structure_assignment()
	if slip.payroll_period:
		slip.remaining_sub_periods = get_period_factor(
			slip.employee,
			slip.start_date,
			slip.end_date,
			slip.payroll_frequency,
			slip.payroll_period,
			joining_date=slip.joining_date,
			relieving_date=slip.relieving_date,
		)[1]


def calculate_income_tax(salary_slip, earnings, deductions):
	"""Income Tax rows and tax breakup for the given component rows, with the Salary Slip's own tax
	logic (add_tax_components + compute_income_tax_breakup) run on an in-memory copy that is never saved.

	Returns (tax_rows, breakup) or (None, None) when the slip has no tax calculation."""
	slip = frappe.get_doc("Salary Slip", salary_slip)
	if not slip.salary_structure or not slip.payroll_period:
		return None, None

	tax_components = {d.salary_component for d in slip.deductions if is_tax_row(d)}
	tax_components |= {d.get("salary_component") for d in deductions if is_tax_row(d)}
	if not tax_components:
		tax_components = set(slip.get_tax_components())  # as for a new Salary Slip
	if not tax_components:
		return None, None

	slip.set("earnings", [{f: r.get(f) for f in DETAIL_FIELDS} for r in earnings])
	slip.set("deductions", [{f: r.get(f) for f in DETAIL_FIELDS} for r in deductions])
	for component in tax_components - {d.salary_component for d in slip.deductions}:
		slip.append("deductions", {**(get_salary_component_data(component) or {}), "amount": 0})

	prepare_tax_context(slip)
	slip.add_tax_components()
	slip.set_precision_for_component_amounts()
	slip.compute_income_tax_breakup()

	tax_rows = [{f: d.get(f) for f in DETAIL_FIELDS} for d in slip.deductions if is_tax_row(d)]
	breakup = {f: flt(slip.get(f), 2) for f in TAX_BREAKUP_FIELDS}
	return tax_rows, breakup


# ---------------------------------------------------------------- dimensions / budget


def get_enabled_dimension_fields(project):
	"""Repost dimension fields enabled for the Project, or None when the Project is not configured."""
	dimensions = get_project_dimensions(project) if project else None
	if dimensions is None:
		return None
	return [DIMENSION_LABEL_FIELD[d] for d in dimensions]


def resolve_budget(employee, employee_name, dimensions):
	"""Payroll budget row for the edited dimensions (same matching as Payroll). Returns (row, error)."""
	values = {"name": employee, "employee_name": employee_name}
	values.update({DIMENSION_FIELDS[f]: dimensions.get(f) for f in DIMENSION_FIELDS})
	return resolve_payroll_budget(values)


# ---------------------------------------------------------------- slip data


def detail_rows(rows):
	return [{f: row.get(f) for f in DETAIL_FIELDS} for row in rows or []]


def fill_component_data(row):
	"""Flags of the Salary Component for a row added on the repost."""
	data = get_salary_component_data(row.salary_component) or {}
	for field in COMPONENT_FLAG_FIELDS:
		row.set(field, data.get(field))
	row.statistical_component = cint(
		frappe.get_cached_value("Salary Component", row.salary_component, "statistical_component")
	)


def calculate_totals(earnings, deductions, total_loan_repayment=0):
	"""Gross / Total Deduction / Net from the final component amounts (components excluded from the
	totals are skipped, as in Salary Slip.get_component_totals)."""
	gross = sum(flt(r.get("amount")) for r in earnings if not cint(r.get("do_not_include_in_total")))
	deduction = sum(
		flt(r.get("amount")) for r in deductions if not cint(r.get("do_not_include_in_total"))
	)
	return frappe._dict(
		gross_pay=flt(gross, 2),
		total_deduction=flt(deduction, 2),
		net_pay=flt(gross - deduction - flt(total_loan_repayment), 2),
	)


def get_slip_state_hash(slip):
	"""Fingerprint of the slip fields a repost changes. A repost prepared on another state is refused."""
	state = {
		"docstatus": slip.docstatus,
		"journal_entry": slip.journal_entry or None,
		"totals": [flt(slip.gross_pay, 2), flt(slip.total_deduction, 2), flt(slip.net_pay, 2)],
		"dimensions": {f: slip.get(sf) or None for f, sf in SLIP_DIMENSION_FIELDS.items()},
		"budget": {f: slip.get(sf) or None for f, sf in SLIP_BUDGET_FIELDS.items()},
		"ss": [
			cint(slip.get("custom_ss_snapshot")),
			cint(slip.get("custom_ss_applicable")),
			flt(slip.get("custom_ss_base_salary"), 2),
			cint(slip.get("custom_ss_hazard")),
		],
		"rows": [
			[key, r.salary_component, flt(r.amount, 2), r.additional_salary or None]
			for key in ("earnings", "deductions")
			for r in slip.get(key)
		],
	}
	return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


def get_employee_dimensions(slip):
	"""Current dimensions of the slip (grade / section come from the Employee, the slip has no field)."""
	emp = frappe.db.get_value("Employee", slip.employee, list(DIMENSION_FIELDS.values()), as_dict=True)
	dimensions = {f: emp.get(ef) for f, ef in DIMENSION_FIELDS.items()}
	for field, slip_field in SLIP_DIMENSION_FIELDS.items():
		if slip.get(slip_field):
			dimensions[field] = slip.get(slip_field)
	return dimensions


# ---------------------------------------------------------------- apply (Repost Payroll)


def apply_repost_to_salary_slip(repost, data, repost_payroll):
	"""Write the prepared state (repost JSON) onto the submitted Salary Slip, without cancelling it."""
	slip = frappe.get_doc("Salary Slip", repost.salary_slip)
	before = frappe.get_doc("Salary Slip", repost.salary_slip)
	meta = slip.meta

	for field, slip_field in SLIP_DIMENSION_FIELDS.items():
		if meta.has_field(slip_field):
			slip.set(slip_field, data["dimensions"].get(field))
	for field, slip_field in SLIP_BUDGET_FIELDS.items():
		slip.set(slip_field, data["budget"].get(field))

	ss = data["social_security"]
	slip.custom_ss_snapshot = 1
	slip.custom_ss_applicable = cint(ss["applicable"])
	slip.custom_ss_base_salary = flt(ss["salary"])
	slip.custom_ss_hazard = cint(ss["hazard"])
	if meta.has_field("custom_is_hazard"):
		slip.custom_is_hazard = cint(ss["hazard"])
	slip.custom_last_repost_payroll = repost_payroll

	for key in ("earnings", "deductions"):
		slip.set(key, [])
		for row in data[key]:
			slip.append(key, row)

	for field, value in ((data.get("income_tax") or {}).get("breakup") or {}).items():
		if meta.has_field(field):
			slip.set(field, value)

	slip.set_precision_for_component_amounts()
	slip.gross_pay = slip.get_component_totals("earnings")
	slip.base_gross_pay = flt(flt(slip.gross_pay) * flt(slip.exchange_rate), slip.precision("base_gross_pay"))
	slip.set_net_pay()

	expected = data["calculated_values"]
	if (
		abs(flt(slip.gross_pay) - flt(expected["gross_pay"])) > 0.01
		or abs(flt(slip.net_pay) - flt(expected["net_pay"])) > 0.01
	):
		frappe.throw(
			_("Salary Slip {0}: recalculated Net Pay {1} does not match the prepared repost {2}.").format(
				frappe.bold(slip.name), slip.net_pay, expected["net_pay"]
			)
		)
	if flt(slip.net_pay) < 0:
		frappe.throw(_("Salary Slip {0}: Net Pay cannot be less than 0.").format(frappe.bold(slip.name)))

	set_cumulative_values(slip)

	slip.modified = now_datetime()
	slip.modified_by = frappe.session.user
	slip.db_update()
	frappe.db.delete(
		"Salary Detail",
		{"parenttype": "Salary Slip", "parent": slip.name, "parentfield": ("in", ["earnings", "deductions"])},
	)
	for key in ("earnings", "deductions"):
		for idx, row in enumerate(slip.get(key), 1):
			row.name = None
			row.idx = idx
			row.db_insert()

	slip._doc_before_save = before
	slip.save_version()  # only when Salary Slip tracks changes; the repost keeps the full audit anyway
	slip.add_comment(
		"Info",
		_("Reposted by {0} through {1}").format(
			frappe.utils.get_link_to_form("Repost Salary Slip", repost.name),
			frappe.utils.get_link_to_form("Repost Payroll", repost_payroll),
		),
	)
	return slip


def set_cumulative_values(slip):
	"""Year / Month to date values of `slip` as of its own period: only the employee's slips that start
	before it are summed. (Salary Slip.compute_year_to_date sums every other slip of the year, which is
	right only when the slip is the latest one; when an earlier slip is reposted the later slips exist.)"""
	period_start, period_end = slip.get_year_to_date_period()
	SS = frappe.qb.DocType("Salary Slip")
	SD = frappe.qb.DocType("Salary Detail")
	prior = (
		(SS.employee == slip.employee)
		& (SS.docstatus == 1)
		& (SS.name != slip.name)
		& (SS.start_date >= period_start)
		& (SS.end_date < period_end)
		& (SS.start_date < slip.start_date)
	)

	net_sum, gross_sum = (
		frappe.qb.from_(SS).select(Sum(SS.net_pay), Sum(SS.gross_pay)).where(prior)
	).run()[0]
	slip.year_to_date = flt(net_sum) + flt(slip.net_pay)
	slip.gross_year_to_date = flt(gross_sum) + flt(slip.gross_pay)

	month_sum = (
		frappe.qb.from_(SS)
		.select(Sum(SS.net_pay))
		.where(
			(SS.employee == slip.employee)
			& (SS.docstatus == 1)
			& (SS.name != slip.name)
			& (SS.start_date >= get_first_day(slip.start_date))
			& (SS.end_date < slip.start_date)
		)
	).run()[0][0]
	slip.month_to_date = flt(month_sum) + flt(slip.net_pay)

	component_sums = dict(
		(
			frappe.qb.from_(SD)
			.inner_join(SS)
			.on(SD.parent == SS.name)
			.select(SD.salary_component, Sum(SD.amount))
			.where(prior & (SD.parenttype == "Salary Slip"))
			.groupby(SD.salary_component)
		).run()
	)
	for key in ("earnings", "deductions"):
		for row in slip.get(key):
			row.year_to_date = flt(component_sums.get(row.salary_component)) + flt(row.amount)


def recalculate_subsequent_salary_slips(employee, after_slip):
	"""Recalculate the cumulative values of every later submitted slip of the employee in the same
	Year-to-Date period, in chronological order. Component amounts are not changed."""
	period_start, period_end = after_slip.get_year_to_date_period()
	later = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": employee,
			"docstatus": 1,
			"name": ("!=", after_slip.name),
			"start_date": (">", after_slip.start_date),
			"end_date": ("<", period_end),
		},
		order_by="start_date asc, creation asc",
		pluck="name",
	)
	fields = ("year_to_date", "gross_year_to_date", "month_to_date")
	for name in later:
		slip = frappe.get_doc("Salary Slip", name)
		old = {f: flt(slip.get(f)) for f in fields}
		old_rows = {row.name: flt(row.year_to_date) for key in ("earnings", "deductions") for row in slip.get(key)}
		set_cumulative_values(slip)

		changed = {f: slip.get(f) for f in fields if abs(flt(slip.get(f)) - old[f]) > 0.001}
		changed.update(get_tax_breakup_changes(slip))
		if changed:
			frappe.db.set_value("Salary Slip", name, changed, update_modified=False)
		for key in ("earnings", "deductions"):
			for row in slip.get(key):
				if abs(flt(row.year_to_date) - old_rows[row.name]) > 0.001:
					frappe.db.set_value(
						"Salary Detail", row.name, "year_to_date", row.year_to_date, update_modified=False
					)
	return later


def get_tax_breakup_changes(slip):
	"""Tax breakup of a later slip after an earlier slip changed (tax deducted till date, CTC, ...).
	The slip's posted tax amount is kept: if the tax logic now gives another amount, the breakup is
	shifted back to the posted one."""
	posted_tax = sum(flt(d.amount) for d in slip.deductions if is_tax_row(d))
	if not any(is_tax_row(d) for d in slip.deductions):
		return {}
	tax_rows, breakup = calculate_income_tax(slip.name, detail_rows(slip.earnings), detail_rows(slip.deductions))
	if not breakup:
		return {}

	difference = posted_tax - sum(flt(r.get("amount")) for r in tax_rows)
	breakup["income_tax_deducted_till_date"] += difference
	breakup["current_month_income_tax"] += difference
	breakup["future_income_tax_deductions"] -= difference
	return {
		f: flt(v, 2)
		for f, v in breakup.items()
		if slip.meta.has_field(f) and abs(flt(v) - flt(slip.get(f))) > 0.005
	}


def to_json(value):
	return json.dumps(value, indent=1, sort_keys=False, default=str)


def date_str(value):
	return str(getdate(value)) if value else None
