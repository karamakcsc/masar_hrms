# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from masar_hrms.payroll_budget.utils import parse_dimensions


class PayrollBudgetSettings(Document):
	def validate(self):
		self.validate_project_dimensions()

	def validate_project_dimensions(self):
		seen = {}
		for row in self.project_dimensions:
			if not row.project:
				frappe.throw(_("Row {0}: Project is mandatory.").format(row.idx))

			if row.project in seen:
				frappe.throw(
					_("Row {0}: Project {1} is already configured in row {2}.").format(
						row.idx, frappe.bold(row.project), seen[row.project]
					)
				)
			seen[row.project] = row.idx

			if not row.enable_multi_dimension:
				row.dimensions = None
				continue

			dimensions = parse_dimensions(row.dimensions)
			if not dimensions:
				frappe.throw(
					_(
						"Row {0}: select at least one dimension for Project {1}, or disable Multi Dimension."
					).format(row.idx, frappe.bold(row.project))
				)
			row.dimensions = ", ".join(dimensions)
