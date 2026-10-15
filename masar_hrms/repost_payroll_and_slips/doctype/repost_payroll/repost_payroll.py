# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

"""Applies every prepared Repost Salary Slip of a Payroll Entry in ONE operation:

validate -> reverse or cancel the existing accrual Journal Entry -> update the Salary Slips ->
recalculate the cumulative values of the later slips -> ONE new consolidated accrual Journal Entry.

Everything runs in the submit transaction: any error rolls the whole repost back."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form, now_datetime

from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry

from masar_hrms.repost_payroll_and_slips.utils import (
	ACTION_CANCEL,
	ACTION_REVERSE,
	apply_repost_to_salary_slip,
	check_repost_permissions,
	recalculate_subsequent_salary_slips,
	validate_accounting_date,
)


class RepostPayroll(Document):
	def validate(self):
		payroll_entry = self.validate_payroll_entry()
		self.set_payroll_details(payroll_entry)
		check_repost_permissions(self.payroll_entry, accounting_action=self.accounting_action)
		if not self.reposts:
			self.set_reposts()
		self.validate_reposts()
		self.set_summary()
		self.status = "Draft"

	def before_submit(self):
		if not self.reposts:
			frappe.throw(_("There is no pending Repost Salary Slip for Payroll Entry {0}.").format(frappe.bold(self.payroll_entry)))
		validate_accounting_date(self.company, self.posting_date)

	def on_submit(self):
		self.process_repost()

	def before_cancel(self):
		frappe.throw(
			_(
				"A completed Repost Payroll cannot be cancelled. Prepare new Repost Salary Slips and run another Repost Payroll to correct it."
			)
		)

	# ------------------------------------------------------------ UI

	@frappe.whitelist()
	def get_reposts(self):
		self.validate_payroll_entry()
		self.set_payroll_details(frappe.get_doc("Payroll Entry", self.payroll_entry))
		self.set_reposts()
		self.set_summary()

	# ------------------------------------------------------------ validation

	def validate_payroll_entry(self):
		payroll_entry = frappe.get_doc("Payroll Entry", self.payroll_entry)
		if payroll_entry.docstatus != 1:
			frappe.throw(_("Payroll Entry {0} must be submitted.").format(frappe.bold(self.payroll_entry)))
		return payroll_entry

	def set_payroll_details(self, payroll_entry):
		self.company = payroll_entry.company
		self.payroll_posting_date = payroll_entry.posting_date
		self.start_date = payroll_entry.start_date
		self.end_date = payroll_entry.end_date
		if not self.posting_date:
			self.posting_date = payroll_entry.posting_date
		self.number_of_salary_slips = frappe.db.count(
			"Salary Slip", {"payroll_entry": self.payroll_entry, "docstatus": 1}
		)

	def set_reposts(self):
		reposts = frappe.get_all(
			"Repost Salary Slip",
			filters={"payroll_entry": self.payroll_entry, "docstatus": 1, "status": "Pending"},
			fields=[
				"name",
				"salary_slip",
				"employee",
				"employee_name",
				"original_gross_pay",
				"gross_pay",
				"original_total_deduction",
				"total_deduction",
				"original_net_pay",
				"net_pay",
			],
			order_by="employee asc",
		)
		self.set("reposts", [])
		for r in reposts:
			self.append(
				"reposts",
				{
					"repost_salary_slip": r.name,
					"salary_slip": r.salary_slip,
					"employee": r.employee,
					"employee_name": r.employee_name,
					"old_gross_pay": r.original_gross_pay,
					"new_gross_pay": r.gross_pay,
					"old_total_deduction": r.original_total_deduction,
					"new_total_deduction": r.total_deduction,
					"old_net_pay": r.original_net_pay,
					"new_net_pay": r.net_pay,
				},
			)

	def validate_reposts(self):
		seen_slips = set()
		for row in self.reposts:
			repost = frappe.db.get_value(
				"Repost Salary Slip",
				row.repost_salary_slip,
				["docstatus", "status", "payroll_entry", "salary_slip"],
				as_dict=True,
			)
			if not repost or repost.docstatus != 1 or repost.status != "Pending":
				frappe.throw(
					_("Row {0}: Repost Salary Slip {1} is not a submitted, pending repost.").format(
						row.idx, frappe.bold(row.repost_salary_slip)
					)
				)
			if repost.payroll_entry != self.payroll_entry:
				frappe.throw(
					_("Row {0}: Repost Salary Slip {1} belongs to Payroll Entry {2}.").format(
						row.idx, frappe.bold(row.repost_salary_slip), frappe.bold(repost.payroll_entry)
					)
				)
			if repost.salary_slip in seen_slips:
				frappe.throw(_("Row {0}: Salary Slip {1} is reposted twice.").format(row.idx, frappe.bold(repost.salary_slip)))
			seen_slips.add(repost.salary_slip)

	def set_summary(self):
		self.number_of_reposts = len(self.reposts)
		self.employees_affected = len({r.employee for r in self.reposts})
		self.old_total_net_pay = sum(flt(r.old_net_pay) for r in self.reposts)
		self.new_total_net_pay = sum(flt(r.new_net_pay) for r in self.reposts)
		self.net_pay_difference = flt(self.new_total_net_pay) - flt(self.old_total_net_pay)

	# ------------------------------------------------------------ processing

	def process_repost(self):
		# one repost at a time per Payroll Entry
		frappe.db.get_value("Payroll Entry", self.payroll_entry, "name", for_update=True)
		payroll_entry = self.validate_payroll_entry()
		check_repost_permissions(self.payroll_entry, accounting_action=self.accounting_action)
		validate_accounting_date(self.company, self.posting_date)

		# 1. validate every repost before touching anything
		reposts = [frappe.get_doc("Repost Salary Slip", r.repost_salary_slip) for r in self.reposts]
		prepared = {repost.name: repost.validate_for_apply() for repost in reposts}

		salary_slips = frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": self.payroll_entry, "docstatus": 1},
			fields=["name", "journal_entry"],
		)
		old_journal_entries = self.validate_existing_journal_entries(salary_slips)

		# 2. old accounting effect
		reversal_entries = []
		if self.accounting_action == ACTION_REVERSE:
			reversal_entries = [self.make_reversal_entry(je) for je in old_journal_entries]
			self.unlink_journal_entries(old_journal_entries)
		elif self.accounting_action == ACTION_CANCEL:
			# delink first: cancelling the Journal Entry must not reach the Salary Slips
			self.unlink_journal_entries(old_journal_entries)
			for je in old_journal_entries:
				journal_entry = frappe.get_doc("Journal Entry", je)
				journal_entry.flags.ignore_permissions = True
				journal_entry.cancel()
		else:
			frappe.throw(_("Select an Accounting Action."))

		# 3. new Salary Slip state + cumulative values of the later slips
		for repost in reposts:
			slip = apply_repost_to_salary_slip(repost, prepared[repost.name], self.name)
			recalculate_subsequent_salary_slips(slip.employee, slip)
			repost.mark_applied(self.name)

		# 4. ONE consolidated accrual Journal Entry for the whole Payroll (Payroll's own logic)
		payroll_entry.posting_date = self.posting_date  # in memory only: date of the new entry
		payroll_entry.make_accrual_jv_entry(submitted_salary_slips=salary_slips)
		new_journal_entry = self.get_new_journal_entry(salary_slips, old_journal_entries)

		self.db_set(
			{
				"status": "Completed",
				"old_journal_entries": "\n".join(old_journal_entries),
				"reversal_journal_entries": "\n".join(reversal_entries),
				"new_journal_entry": new_journal_entry,
				"completed_on": now_datetime(),
				"completed_by": frappe.session.user,
			}
		)
		self.add_audit_comments(new_journal_entry, old_journal_entries, reversal_entries)
		self.warn_if_paid(payroll_entry)

	def validate_existing_journal_entries(self, salary_slips):
		if not salary_slips:
			frappe.throw(_("Payroll Entry {0} has no submitted Salary Slip.").format(frappe.bold(self.payroll_entry)))

		unlinked = [s.name for s in salary_slips if not s.journal_entry]
		if unlinked:
			frappe.throw(
				_("These Salary Slips of Payroll Entry {0} have no accrual Journal Entry: {1}").format(
					frappe.bold(self.payroll_entry), ", ".join(unlinked[:20])
				),
				title=_("Accrual Missing"),
			)

		journal_entries = sorted({s.journal_entry for s in salary_slips})
		for je in journal_entries:
			docstatus, posting_date = frappe.db.get_value("Journal Entry", je, ["docstatus", "posting_date"])
			if docstatus != 1:
				frappe.throw(_("Journal Entry {0} linked to the Salary Slips is not submitted.").format(frappe.bold(je)))
			if self.accounting_action == ACTION_CANCEL:
				# cancelling posts on the original date: it must still be open
				validate_accounting_date(self.company, posting_date, _("Journal Entry {0} Posting Date").format(je))
		return journal_entries

	def make_reversal_entry(self, journal_entry):
		reversal = make_reverse_journal_entry(journal_entry)
		reversal.posting_date = self.posting_date
		reversal.user_remark = _("Reversal of {0} by Repost Payroll {1} (Payroll Entry {2})").format(
			journal_entry, self.name, self.payroll_entry
		)
		reversal.flags.ignore_permissions = True
		reversal.insert()
		reversal.submit()
		return reversal.name

	def unlink_journal_entries(self, journal_entries):
		SalarySlip = frappe.qb.DocType("Salary Slip")
		(
			frappe.qb.update(SalarySlip)
			.set(SalarySlip.journal_entry, None)
			.where(
				(SalarySlip.payroll_entry == self.payroll_entry)
				& (SalarySlip.docstatus == 1)
				& (SalarySlip.journal_entry.isin(journal_entries))
			)
		).run()

	def get_new_journal_entry(self, salary_slips, old_journal_entries):
		linked = set(
			frappe.get_all(
				"Salary Slip",
				filters={"name": ("in", [s.name for s in salary_slips])},
				pluck="journal_entry",
			)
		)
		if len(linked) != 1 or not next(iter(linked)) or linked & set(old_journal_entries):
			frappe.throw(_("The new accrual Journal Entry was not linked to every Salary Slip of the Payroll Entry."))
		return linked.pop()

	def add_audit_comments(self, new_journal_entry, old_journal_entries, reversal_entries):
		old_action = (
			_("reversed by {0}").format(", ".join(reversal_entries))
			if reversal_entries
			else _("cancelled")
		)
		message = _("Repost Payroll {0}: {1} Salary Slip(s) reposted. Journal Entry {2} {3}. New Journal Entry {4}.").format(
			get_link_to_form(self.doctype, self.name),
			len(self.reposts),
			", ".join(old_journal_entries),
			old_action,
			get_link_to_form("Journal Entry", new_journal_entry),
		)
		frappe.get_doc("Payroll Entry", self.payroll_entry).add_comment("Info", message)
		frappe.get_doc("Journal Entry", new_journal_entry).add_comment("Info", message)

	def warn_if_paid(self, payroll_entry):
		if abs(flt(self.net_pay_difference)) < 0.005:
			return
		if payroll_entry.has_bank_entries().get("has_bank_entries"):
			frappe.msgprint(
				_(
					"A Bank Entry was already made for Payroll Entry {0}. The Net Pay changed by {1}: settle the "
					"difference on the Payroll Payable account manually."
				).format(frappe.bold(self.payroll_entry), frappe.bold(frappe.format(self.net_pay_difference, "Currency"))),
				title=_("Payroll Already Paid"),
				indicator="orange",
			)
