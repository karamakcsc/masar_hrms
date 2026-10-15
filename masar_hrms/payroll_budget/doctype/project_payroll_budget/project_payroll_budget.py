# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from masar_hrms.payroll_budget.utils import (
	PAYROLL_DIMENSIONS,
	SETTINGS_DOCTYPE,
	get_dimension_key,
	get_project_dimensions,
)


class ProjectPayrollBudget(Document):
	def validate(self):
		self.validate_unique_project()
		dimensions = get_project_dimensions(self.project)
		if dimensions is None:
			frappe.throw(
				_("Project {0} is not configured in {1}.").format(frappe.bold(self.project), SETTINGS_DOCTYPE)
			)
		self.enabled_dimensions = ", ".join(dimensions) if dimensions else _("None (Project only)")
		self.validate_budget_dimensions(dimensions)

	def validate_unique_project(self):
		existing = frappe.db.get_value(
			self.doctype, {"project": self.project, "name": ("!=", self.name)}, "name"
		)
		if existing:
			frappe.throw(
				_("Project {0} already has a {1}: {2}").format(
					frappe.bold(self.project), self.doctype, frappe.get_desk_link(self.doctype, existing)
				)
			)

	def validate_budget_dimensions(self, dimensions):
		if not dimensions and len(self.budget_dimensions) > 1:
			frappe.throw(
				_("Project {0} has no dimensions enabled, so only one budget row is allowed.").format(
					frappe.bold(self.project)
				)
			)

		disabled_fields = [
			d["budget_field"] for label, d in PAYROLL_DIMENSIONS.items() if label not in dimensions
		]
		seen = {}
		for row in self.budget_dimensions:
			# Dimensions not enabled for this Project are never part of the combination
			for fieldname in disabled_fields:
				row.set(fieldname, None)

			missing = [d for d in dimensions if not row.get(PAYROLL_DIMENSIONS[d]["budget_field"])]
			if missing:
				frappe.throw(
					_("Row {0}: {1} is mandatory for Project {2}.").format(
						row.idx, ", ".join(missing), frappe.bold(self.project)
					)
				)

			key = get_dimension_key(row, dimensions, "budget_field")
			if key in seen:
				combination = ", ".join(f"{d} = {v}" for d, v in zip(dimensions, key))
				frappe.throw(
					_("Row {0}: duplicate dimension combination [{1}], already defined in row {2}.").format(
						row.idx, combination, seen[key]
					),
					title=_("Duplicate Budget Dimension"),
				)
			seen[key] = row.idx
