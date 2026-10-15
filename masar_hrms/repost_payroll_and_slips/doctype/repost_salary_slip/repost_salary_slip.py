# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

"""Prepares the new state of one submitted Salary Slip. Has NO accounting effect: the prepared
state is stored as JSON and applied, with every other repost of the Payroll Entry, by Repost Payroll."""

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, fmt_money, get_link_to_form, now_datetime, nowdate

from masar_hrms.payroll_budget.utils import is_payroll_budget_enabled
from masar_hrms.repost_payroll_and_slips.utils import (
	DETAIL_FIELDS,
	DIMENSION_FIELDS,
	REPOST_JSON_VERSION,
	SLIP_BUDGET_FIELDS,
	TAX_BREAKUP_FIELDS,
	calculate_income_tax,
	calculate_social_security,
	calculate_totals,
	check_repost_permissions,
	date_str,
	detail_rows,
	fill_component_data,
	get_employee_dimensions,
	get_enabled_dimension_fields,
	get_original_social_security,
	get_slip_state_hash,
	get_social_security_component,
	is_tax_row,
	resolve_budget,
	sync_row_amounts,
	to_json,
	validate_accounting_date,
)

SLIP_FIELDS = (
	"employee",
	"employee_name",
	"payroll_entry",
	"company",
	"posting_date",
	"start_date",
	"end_date",
	"salary_structure",
	"currency",
	"exchange_rate",
	"total_working_days",
	"payment_days",
	"leave_without_pay",
	"absent_days",
	"total_loan_repayment",
)
# Select dimensions: options are read from the Employee field
SELECT_DIMENSIONS = {"section": "custom_section", "work_type": "work_type"}
# Values compared between two preparations of the same repost (see validate_for_apply)
APPLY_COMPARE_KEYS = (
	"dimensions",
	"budget",
	"social_security",
	"income_tax",
	"earnings",
	"deductions",
	"calculated_values",
)


class RepostSalarySlip(Document):
	def validate(self):
		slip = self.validate_salary_slip()
		check_repost_permissions(self.payroll_entry, self.salary_slip)
		self.validate_duplicate()
		if not self.original_data or json.loads(self.original_data).get("salary_slip") != self.salary_slip:
			self.set_from_salary_slip(slip)
		self.validate_accounting_period()
		self.calculate()
		self.repost_data = to_json(self.get_repost_data())
		self.set_changes()
		self.status = "Draft"

	def before_submit(self):
		self.validate_salary_slip_unchanged()
		if not self.changes:
			frappe.throw(_("Nothing to repost: the prepared values are the same as the Salary Slip."))

	def on_submit(self):
		self.db_set("status", "Pending")

	def before_cancel(self):
		if self.status == "Applied":
			frappe.throw(
				_("Repost {0} is already applied by {1} and cannot be cancelled.").format(
					frappe.bold(self.name), frappe.bold(self.repost_payroll)
				)
			)
		pending_payroll = frappe.db.get_value(
			"Repost Payroll Item",
			{"repost_salary_slip": self.name, "docstatus": 0, "parenttype": "Repost Payroll"},
			"parent",
		)
		if pending_payroll:
			frappe.throw(
				_("Remove this repost from draft Repost Payroll {0} before cancelling it.").format(
					frappe.bold(pending_payroll)
				)
			)

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	# ------------------------------------------------------------ UI

	@frappe.whitelist()
	def load_salary_slip(self):
		slip = self.validate_salary_slip()
		self.set_from_salary_slip(slip)
		self.calculate(raise_exception=False)

	@frappe.whitelist()
	def recalculate(self):
		self.calculate(raise_exception=False)

	# ------------------------------------------------------------ validation

	def validate_salary_slip(self):
		if not self.salary_slip:
			frappe.throw(_("Salary Slip is required."))
		slip = frappe.get_doc("Salary Slip", self.salary_slip)
		if slip.docstatus != 1:
			frappe.throw(_("Salary Slip {0} must be submitted.").format(frappe.bold(slip.name)))
		if not slip.payroll_entry:
			frappe.throw(_("Salary Slip {0} is not linked to a Payroll Entry.").format(frappe.bold(slip.name)))
		if frappe.db.get_value("Payroll Entry", slip.payroll_entry, "docstatus") != 1:
			frappe.throw(_("Payroll Entry {0} must be submitted.").format(frappe.bold(slip.payroll_entry)))
		if not slip.journal_entry:
			frappe.throw(
				_(
					"Salary Slip {0} has no accrual Journal Entry. Make the Payroll accounting entry before reposting."
				).format(frappe.bold(slip.name))
			)
		return slip

	def validate_duplicate(self):
		existing = frappe.db.get_value(
			"Repost Salary Slip",
			{
				"salary_slip": self.salary_slip,
				"docstatus": ("<", 2),
				"status": ("!=", "Applied"),
				"name": ("!=", self.name),
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("Repost Salary Slip {0} is already prepared for Salary Slip {1}.").format(
					get_link_to_form("Repost Salary Slip", existing), frappe.bold(self.salary_slip)
				),
				title=_("Duplicate Repost"),
			)

	def validate_accounting_period(self):
		"""No accounting here, but a repost that Repost Payroll could never post is refused: the Payroll
		posting date must be open, or at least today (Repost Payroll can post a reversal later)."""
		try:
			validate_accounting_date(self.company, self.posting_date, _("Payroll Posting Date"))
		except frappe.ValidationError as payroll_date_error:
			frappe.clear_messages()
			try:
				validate_accounting_date(self.company, nowdate(), _("Today"))
			except frappe.ValidationError:
				frappe.clear_messages()
				frappe.throw(str(payroll_date_error), title=_("Accounting Period Closed"))
			frappe.msgprint(
				_(
					"The Payroll posting date {0} is closed for accounting. Repost Payroll will have to use the "
					"<b>Reverse Existing Journal Entry</b> action with an open posting date."
				).format(frappe.bold(frappe.format(self.posting_date, "Date"))),
				indicator="orange",
				alert=True,
			)

	def validate_salary_slip_unchanged(self):
		slip = frappe.get_doc("Salary Slip", self.salary_slip)
		if get_slip_state_hash(slip) != self.source_hash:
			frappe.throw(
				_(
					"Salary Slip {0} changed after this repost was prepared. Cancel/amend the repost and reload the Salary Slip."
				).format(frappe.bold(self.salary_slip)),
				title=_("Salary Slip Changed"),
			)

	def validate_for_apply(self):
		"""Called by Repost Payroll: the slip is still in the prepared state and preparing the repost
		again, with today's Payroll configuration, gives the same result."""
		if self.docstatus != 1 or self.status != "Pending":
			frappe.throw(_("Repost Salary Slip {0} is not pending.").format(frappe.bold(self.name)))
		self.validate_salary_slip()
		self.validate_salary_slip_unchanged()

		stored = json.loads(self.repost_data)
		self.calculate()
		current = json.loads(to_json(self.get_repost_data()))
		changed = [k for k in APPLY_COMPARE_KEYS if stored.get(k) != current.get(k)]
		if changed:
			frappe.throw(
				_(
					"Repost Salary Slip {0}: {1} changed since it was prepared (Payroll Budget, Social Security or Company "
					"configuration). Cancel and amend it to prepare it again."
				).format(frappe.bold(self.name), ", ".join(changed)),
				title=_("Repost Out of Date"),
			)
		return stored

	# ------------------------------------------------------------ load

	def set_from_salary_slip(self, slip):
		for field in SLIP_FIELDS:
			self.set(field, slip.get(field))
		self.salary_structure_assignment = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": slip.employee,
				"salary_structure": slip.salary_structure,
				"from_date": ("<=", slip.start_date),
				"docstatus": 1,
			},
			"name",
			order_by="from_date desc",
		)

		for field, value in get_employee_dimensions(slip).items():
			self.set(field, value)
		for field, slip_field in SLIP_BUDGET_FIELDS.items():
			self.set(field, slip.get(slip_field))

		ss = get_original_social_security(slip)
		self.is_social_security_applicable = ss.applicable
		self.social_security_salary = ss.salary
		self.is_hazard = ss.hazard

		ss_component = get_social_security_component(self.salary_structure)
		for key in ("earnings", "deductions"):
			self.set(key, [])
			for row in slip.get(key):
				values = {f: row.get(f) for f in DETAIL_FIELDS}
				values.update(
					year_to_date=row.year_to_date,
					original_amount=row.amount,
					is_social_security=cint(key == "deductions" and row.salary_component == ss_component),
					is_income_tax=cint(key == "deductions" and is_tax_row(row)),
				)
				self.append(key, values)

		self.original_gross_pay = slip.gross_pay
		self.original_total_deduction = slip.total_deduction
		self.original_net_pay = slip.net_pay
		self.gross_pay, self.total_deduction, self.net_pay = slip.gross_pay, slip.total_deduction, slip.net_pay

		ss_values = calculate_social_security(
			self.company, self.employee, self.payment_days, ss.applicable, ss.salary, ss.hazard
		)
		self.employee_share_rate, self.company_share_rate = ss_values.employee_rate, ss_values.company_rate
		self.employee_social_security = sum(flt(d.amount) for d in self.deductions if d.is_social_security)
		self.company_social_security = ss_values.company_amount

		self.income_tax = self.original_income_tax = sum(flt(d.amount) for d in self.deductions if d.is_income_tax)
		self.annual_taxable_amount = slip.get("annual_taxable_amount")
		self._tax_breakup = {f: flt(slip.get(f), 2) for f in TAX_BREAKUP_FIELDS}

		self.source_hash = get_slip_state_hash(slip)
		self.original_data = to_json(self.get_repost_data())

	# ------------------------------------------------------------ calculation

	def calculate(self, raise_exception=True):
		errors = []
		self.set_budget(errors)
		self.set_components(errors)
		self.set_social_security(errors)
		self.set_income_tax(errors)
		self.set_totals(errors)

		if errors:
			message = "<br>".join(errors)
			if raise_exception:
				frappe.throw(message, title=_("Repost Validation Failed"))
			frappe.msgprint(message, title=_("Repost Validation"), indicator="orange")

	def set_budget(self, errors):
		original = json.loads(self.original_data or "{}")
		original_dimensions = original.get("dimensions") or {}
		enabled = get_enabled_dimension_fields(self.project)
		self.enabled_dimensions = ", ".join(enabled or [])

		for field, employee_field in SELECT_DIMENSIONS.items():
			options = (frappe.get_meta("Employee").get_options(employee_field) or "").split("\n")
			if self.get(field) and self.get(field) not in options:
				errors.append(_("{0} {1} is not a valid option.").format(_(field.title()), frappe.bold(self.get(field))))

		if not is_payroll_budget_enabled():
			return

		if not self.project:
			errors.append(_("Project is required."))
			return
		if enabled is None:
			errors.append(
				_("Project {0} is not configured in Payroll Budget Settings.").format(frappe.bold(self.project))
			)
			return

		for field in DIMENSION_FIELDS:
			if field == "project" or field in enabled:
				continue
			if (self.get(field) or None) != (original_dimensions.get(field) or None):
				errors.append(
					_("{0} is not a Payroll Budget dimension of Project {1} and cannot be changed.").format(
						frappe.bold(self.meta.get_label(field)), frappe.bold(self.project)
					)
				)

		budget, error = resolve_budget(
			self.employee, self.employee_name, {f: self.get(f) for f in DIMENSION_FIELDS}
		)
		if error:
			errors.append(error)
			budget = frappe._dict()
		for field in SLIP_BUDGET_FIELDS:
			self.set(field, budget.get(field))

		if budget and not budget.salary_budget_element:
			errors.append(_("No Salary Budget Element is set on the matching Project Payroll Budget row."))
		if budget and not budget.salary_cost_center:
			errors.append(_("Salary Budget Element {0} has no Cost Center.").format(frappe.bold(budget.salary_budget_element)))
		if budget and self.is_social_security_applicable and not budget.ss_budget_element:
			errors.append(_("No Company Social Security Budget Element is set on the matching Project Payroll Budget row."))
		if budget and budget.ss_budget_element and not budget.ss_cost_center:
			errors.append(_("Company Social Security Budget Element {0} has no Cost Center.").format(frappe.bold(budget.ss_budget_element)))

	def set_components(self, errors):
		original = json.loads(self.original_data or "{}")
		original_rows = {
			(key, r["salary_component"], r.get("additional_salary") or None): r
			for key in ("earnings", "deductions")
			for r in original.get(key) or []
		}
		for key, component_type in (("earnings", "Earning"), ("deductions", "Deduction")):
			for row in self.get(key):
				if not row.salary_component:
					errors.append(_("Row {0} in {1}: Component is required.").format(row.idx, _(key.title())))
					continue
				actual_type = frappe.get_cached_value("Salary Component", row.salary_component, "type")
				if actual_type != component_type:
					errors.append(
						_("Row {0} in {1}: {2} is not an {3} component.").format(
							row.idx, _(key.title()), frappe.bold(row.salary_component), _(component_type)
						)
					)
				if flt(row.amount) < 0:
					errors.append(_("Row {0} in {1}: Amount cannot be negative.").format(row.idx, _(key.title())))
				if not row.abbr:
					fill_component_data(row)
				row.is_income_tax = cint(key == "deductions" and is_tax_row(row))
				if row.is_income_tax or row.is_social_security:
					continue  # calculated below
				original_row = original_rows.get((key, row.salary_component, row.additional_salary or None))
				if original_row and abs(flt(row.amount) - flt(original_row.get("amount"))) < 0.005:
					# unchanged: keep the slip's own default / additional amount
					row.default_amount = original_row.get("default_amount")
					row.additional_amount = original_row.get("additional_amount")
				else:
					sync_row_amounts(row, self.payment_days, self.total_working_days)

	def set_social_security(self, errors):
		"""Employee Social Security row and Company share are calculated, never typed. When the Social
		Security input is unchanged the slip's own Social Security deduction is kept."""
		original = frappe._dict(json.loads(self.original_data or "{}").get("social_security") or {})
		ss_component = get_social_security_component(self.salary_structure)
		ss_changed = (
			cint(self.is_social_security_applicable),
			flt(self.social_security_salary, 2),
			cint(self.is_hazard),
		) != (cint(original.applicable), flt(original.salary, 2), cint(original.hazard))

		values = calculate_social_security(
			self.company,
			self.employee,
			self.payment_days,
			self.is_social_security_applicable,
			self.social_security_salary,
			self.is_hazard,
		)
		self.employee_share_rate, self.company_share_rate = values.employee_rate, values.company_rate
		self.company_social_security = flt(values.company_amount, 2)

		if not ss_component:
			self.employee_social_security = 0
			if ss_changed and values.employee_amount:
				errors.append(_("No Social Security deduction component (formula social_security_amount) was found."))
			return

		original_rows = [
			frappe._dict(r)
			for r in json.loads(self.original_data or "{}").get("deductions") or []
			if r.get("salary_component") == ss_component
		]
		original_amount = sum(flt(r.amount) for r in original_rows)
		amount = flt(values.employee_amount, 2) if ss_changed else original_amount

		rows, position = [], None
		for row in self.deductions:
			if row.salary_component == ss_component:
				position = len(rows) if position is None else position
			else:
				rows.append(row)

		if amount or (original_rows and not ss_changed):
			values = dict(original_rows[0]) if original_rows else {"salary_component": ss_component}
			values.update(amount=amount, original_amount=original_amount, is_social_security=1)
			if not original_rows:
				values["default_amount"] = amount
			ss_row = frappe.get_doc({**values, "doctype": "Repost Salary Detail"})
			if not ss_row.abbr:
				fill_component_data(ss_row)
			rows.insert(len(rows) if position is None else position, ss_row)

		self.set("deductions", rows)
		for idx, row in enumerate(self.deductions, 1):
			row.idx = idx
		self.employee_social_security = amount

	def set_income_tax(self, errors):
		"""Income Tax rows are calculated by the Salary Slip tax logic from the final earnings, never typed
		(the Salary Slip itself recalculates them on validate)."""
		self._tax_breakup = {}
		try:
			tax_rows, breakup = calculate_income_tax(
				self.salary_slip, detail_rows(self.earnings), detail_rows(self.deductions)
			)
		except frappe.ValidationError as e:
			errors.append(_("Income Tax: {0}").format(str(e)))
			return
		if tax_rows is None:
			self.income_tax = sum(flt(d.amount) for d in self.deductions if d.is_income_tax)
			return

		original_amounts = {}
		for r in json.loads(self.original_data or "{}").get("deductions") or []:
			if is_tax_row(r):
				original_amounts[r["salary_component"]] = flt(original_amounts.get(r["salary_component"])) + flt(r.get("amount"))

		rows, position = [], None
		for row in self.deductions:
			if is_tax_row(row):
				position = len(rows) if position is None else position
			else:
				rows.append(row)
		position = len(rows) if position is None else position
		for values in tax_rows:
			tax_row = frappe.get_doc({**values, "doctype": "Repost Salary Detail"})
			tax_row.update({"original_amount": original_amounts.get(tax_row.salary_component, 0), "is_income_tax": 1})
			rows.insert(position, tax_row)
			position += 1

		self.set("deductions", rows)
		for idx, row in enumerate(self.deductions, 1):
			row.idx = idx
		self.income_tax = sum(flt(r.get("amount")) for r in tax_rows)
		self.annual_taxable_amount = breakup.get("annual_taxable_amount")
		self._tax_breakup = breakup

	def set_totals(self, errors):
		totals = calculate_totals(self.earnings, self.deductions, self.total_loan_repayment)
		self.update(totals)
		self.net_pay_difference = flt(self.net_pay) - flt(self.original_net_pay)
		if flt(self.net_pay) < 0:
			errors.append(_("Net Pay cannot be less than 0."))

	# ------------------------------------------------------------ JSON / audit

	def get_repost_data(self):
		return {
			"version": REPOST_JSON_VERSION,
			"repost_salary_slip": self.name,
			"salary_slip": self.salary_slip,
			"employee": self.employee,
			"employee_name": self.employee_name,
			"payroll_entry": self.payroll_entry,
			"company": self.company,
			"posting_date": date_str(self.posting_date),
			"start_date": date_str(self.start_date),
			"end_date": date_str(self.end_date),
			"currency": self.currency,
			"exchange_rate": flt(self.exchange_rate),
			"salary_structure": self.salary_structure,
			"salary_structure_assignment": self.salary_structure_assignment,
			"working_days": {
				"total_working_days": flt(self.total_working_days),
				"payment_days": flt(self.payment_days),
				"leave_without_pay": flt(self.leave_without_pay),
				"absent_days": flt(self.absent_days),
			},
			"dimensions": {f: self.get(f) or None for f in DIMENSION_FIELDS},
			"enabled_dimensions": [d.strip() for d in (self.enabled_dimensions or "").split(",") if d.strip()],
			"budget": {f: self.get(f) or None for f in SLIP_BUDGET_FIELDS},
			"social_security": {
				"component": get_social_security_component(self.salary_structure),
				"applicable": cint(self.is_social_security_applicable),
				"salary": flt(self.social_security_salary, 2),
				"hazard": cint(self.is_hazard),
				"employee_rate": flt(self.employee_share_rate),
				"company_rate": flt(self.company_share_rate),
				"employee_amount": flt(self.employee_social_security, 2),
				"company_amount": flt(self.company_social_security, 2),
			},
			"income_tax": {
				"amount": flt(self.income_tax, 2),
				"breakup": getattr(self, "_tax_breakup", None) or {},  # set by load / set_income_tax
			},
			"hazard": bool(cint(self.is_hazard)),
			"earnings": detail_rows(self.earnings),
			"deductions": detail_rows(self.deductions),
			"calculated_values": {
				"gross_pay": flt(self.gross_pay, 2),
				"total_deduction": flt(self.total_deduction, 2),
				"total_loan_repayment": flt(self.total_loan_repayment, 2),
				"net_pay": flt(self.net_pay, 2),
			},
			"source_hash": self.source_hash,
		}

	def set_changes(self):
		original = json.loads(self.original_data)
		new = json.loads(self.repost_data)
		changes = []
		# Drafts prepared before the income_tax block existed have no such key in their snapshot.
		original_tax, new_tax = original.get("income_tax") or {}, new.get("income_tax") or {}

		def add(section, field, old, value):
			if (old or None) != (value or None) and not (
				isinstance(old, (int, float)) and isinstance(value, (int, float)) and abs(old - value) < 0.005
			):
				changes.append({"section": section, "field": field, "old_value": _str(old), "new_value": _str(value)})

		for field in DIMENSION_FIELDS:
			add(_("Dimension"), self.meta.get_label(field), original["dimensions"].get(field), new["dimensions"].get(field))
		for field in SLIP_BUDGET_FIELDS:
			add(_("Budget"), self.meta.get_label(field), original["budget"].get(field), new["budget"].get(field))
		for field, label in (
			("applicable", "Social Security Applicable"),
			("salary", "Social Security Salary"),
			("hazard", "Is Hazard"),
			("employee_amount", "Employee Social Security"),
			("company_amount", "Company Social Security"),
		):
			add(_("Social Security"), _(label), original["social_security"].get(field), new["social_security"].get(field))
		for field, label in (("amount", "Income Tax"),):
			add(_("Income Tax"), _(label), original_tax.get(field), new_tax.get(field))
		for field in ("annual_taxable_amount", "income_tax_deducted_till_date"):
			add(
				_("Income Tax"),
				frappe.get_meta("Salary Slip").get_label(field),
				(original_tax.get("breakup") or {}).get(field),
				(new_tax.get("breakup") or {}).get(field),
			)
		for key, section in (("earnings", _("Earning")), ("deductions", _("Deduction"))):
			old_amounts, new_amounts = _component_amounts(original[key]), _component_amounts(new[key])
			for component in list(dict.fromkeys(list(old_amounts) + list(new_amounts))):
				add(section, component, old_amounts.get(component), new_amounts.get(component))
		for field, label in (("gross_pay", "Gross Pay"), ("total_deduction", "Total Deduction"), ("net_pay", "Net Pay")):
			add(_("Totals"), _(label), original["calculated_values"].get(field), new["calculated_values"].get(field))

		self.set("changes", changes)

	def mark_applied(self, repost_payroll):
		self.db_set(
			{
				"status": "Applied",
				"repost_payroll": repost_payroll,
				"applied_on": now_datetime(),
				"applied_by": frappe.session.user,
			}
		)


def _component_amounts(rows):
	amounts = {}
	for row in rows:
		amounts[row["salary_component"]] = flt(amounts.get(row["salary_component"])) + flt(row.get("amount"))
	return amounts


def _str(value):
	if value is None or value == "":
		return ""
	if isinstance(value, float):
		return fmt_money(value, precision=2)
	return str(value)


@frappe.whitelist()
def get_dimension_options():
	"""Options of the Select dimensions, read from the Employee fields."""
	meta = frappe.get_meta("Employee")
	return {field: meta.get_options(employee_field) or "" for field, employee_field in SELECT_DIMENSIONS.items()}


@frappe.whitelist()
def get_enabled_dimensions(project=None):
	enabled = get_enabled_dimension_fields(project)
	return {
		"budget_enabled": is_payroll_budget_enabled(),
		"configured": enabled is not None,
		"dimensions": enabled or [],
		"all_dimensions": [f for f in DIMENSION_FIELDS if f != "project"],
	}
