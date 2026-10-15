# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

"""Dynamic, Project-driven Payroll Budget resolution.

Payroll Budget Settings  -> which dimensions are active for each Project
Project Payroll Budget   -> dimension combinations + Salary / Company Social Security budgets
Employee                 -> Project + dimension values

Nothing here is hard-coded per Project: every lookup is keyed on the dimensions
the Settings enable for the employee's Project.
"""

import frappe
from frappe import _

# Dimension label (as stored in Payroll Budget Settings) -> fieldnames
PAYROLL_DIMENSIONS = {
	"Department": {"employee_field": "department", "budget_field": "department"},
	"Designation": {"employee_field": "designation", "budget_field": "designation"},
	"Branch": {"employee_field": "branch", "budget_field": "branch"},
	"Grade": {"employee_field": "grade", "budget_field": "grade"},
	"Section": {"employee_field": "custom_section", "budget_field": "section"},
	"Work Type": {"employee_field": "work_type", "budget_field": "work_type"},
}

EMPLOYEE_PROJECT_FIELD = "custom_project"
SETTINGS_DOCTYPE = "Payroll Budget Settings"
BUDGET_DOCTYPE = "Project Payroll Budget"
BUDGET_ROW_DOCTYPE = "Payroll Budget Dimensions"


def is_payroll_budget_enabled() -> bool:
	return bool(frappe.get_cached_doc(SETTINGS_DOCTYPE).enable_payroll_budget)


def parse_dimensions(value) -> list[str]:
	"""'Department, Section' (or a list) -> ['Department', 'Section'] in canonical order.
	Unknown labels raise."""
	if not value:
		return []
	if isinstance(value, str):
		value = value.replace("\n", ",").split(",")

	canonical = {d.lower(): d for d in PAYROLL_DIMENSIONS}
	values = {v.strip() for v in value if v and v.strip()}
	selected = {canonical.get(v.lower(), v) for v in values}
	unknown = selected - set(PAYROLL_DIMENSIONS)
	if unknown:
		frappe.throw(
			_("Invalid Payroll Budget dimension(s): {0}. Allowed: {1}").format(
				", ".join(sorted(unknown)), ", ".join(PAYROLL_DIMENSIONS)
			)
		)
	return [d for d in PAYROLL_DIMENSIONS if d in selected]


def get_dimension_settings() -> dict:
	"""{project: [enabled dimension labels]} for every Project in Payroll Budget Settings."""
	settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
	return {
		row.project: parse_dimensions(row.dimensions) if row.enable_multi_dimension else []
		for row in settings.get("project_dimensions") or []
		if row.project
	}


def get_project_dimensions(project) -> list[str] | None:
	"""Enabled dimensions for a Project, or None when the Project is not configured."""
	return get_dimension_settings().get(project)


def get_dimension_key(doc, dimensions, field_key) -> tuple:
	"""Tuple of the values of the enabled dimensions, read with `field_key`
	('employee_field' or 'budget_field')."""
	return tuple((doc.get(PAYROLL_DIMENSIONS[d][field_key]) or "") for d in dimensions)


@frappe.whitelist()
def get_project_dimension_config(project):
	dimensions = get_project_dimensions(project) if project else None
	return {
		"configured": dimensions is not None,
		"dimensions": dimensions or [],
		"budget_fields": {d: PAYROLL_DIMENSIONS[d]["budget_field"] for d in PAYROLL_DIMENSIONS},
	}


def get_budget_rows_by_project(projects) -> dict:
	"""{project: [budget rows]} with Cost Center / Project read live from the Budget Elements."""
	projects = [p for p in set(projects) if p]
	if not projects:
		return {}

	PPB = frappe.qb.DocType(BUDGET_DOCTYPE)
	Row = frappe.qb.DocType(BUDGET_ROW_DOCTYPE)
	SalaryBE = frappe.qb.DocType("Budget Element").as_("salary_be")
	SSBE = frappe.qb.DocType("Budget Element").as_("ss_be")

	rows = (
		frappe.qb.from_(Row)
		.join(PPB)
		.on((PPB.name == Row.parent) & (Row.parenttype == BUDGET_DOCTYPE))
		.left_join(SalaryBE)
		.on(SalaryBE.name == Row.employee_salary_budget)
		.left_join(SSBE)
		.on(SSBE.name == Row.company_social_security_budget)
		.select(
			PPB.project,
			Row.name.as_("budget_row"),
			Row.idx,
			*[Row[d["budget_field"]] for d in PAYROLL_DIMENSIONS.values()],
			Row.employee_salary_budget.as_("salary_budget_element"),
			SalaryBE.cost_center.as_("salary_cost_center"),
			SalaryBE.project.as_("salary_project"),
			Row.company_social_security_budget.as_("ss_budget_element"),
			SSBE.cost_center.as_("ss_cost_center"),
			SSBE.project.as_("ss_project"),
		)
		.where(PPB.project.isin(projects))
		.orderby(Row.idx)
	).run(as_dict=True)

	by_project = {}
	for row in rows:
		# Project fallback: a Budget Element without a Project posts to the budget's Project
		row.salary_project = row.salary_project or row.project
		row.ss_project = row.ss_project or row.project
		by_project.setdefault(row.project, []).append(row)
	return by_project


def get_employee_payroll_budgets(employees, raise_exception=True):
	"""Resolve the Salary / Company Social Security budget of each employee.

	Returns (budgets, errors): budgets = {employee: row}, errors = [message].
	Everything is fetched in bulk (3 queries whatever the number of employees)."""
	employees = list({e for e in employees if e})
	if not employees:
		return {}, []

	emp_fields = ["name", "employee_name", EMPLOYEE_PROJECT_FIELD] + [
		d["employee_field"] for d in PAYROLL_DIMENSIONS.values()
	]
	employee_rows = frappe.get_all("Employee", filters={"name": ["in", employees]}, fields=emp_fields)

	dimension_settings = get_dimension_settings()
	budget_rows = get_budget_rows_by_project(e.get(EMPLOYEE_PROJECT_FIELD) for e in employee_rows)

	budgets, errors = {}, []
	for emp in employee_rows:
		budget, error = _match_employee_budget(emp, dimension_settings, budget_rows)
		if error:
			errors.append(error)
		else:
			budgets[emp.name] = budget

	if errors and raise_exception:
		frappe.throw(
			"<br>".join(errors),
			title=_("Payroll Budget Validation Failed"),
		)

	return budgets, errors


def resolve_payroll_budget(values):
	"""Resolve the budget row for an Employee-like dict (name, employee_name, custom_project and the
	employee dimension fields) with the same matching rules as Payroll. Used by Repost Salary Slip,
	where the dimensions are edited on the repost instead of read from the Employee.

	Returns (budget_row, error)."""
	values = frappe._dict(values)
	project = values.get(EMPLOYEE_PROJECT_FIELD)
	return _match_employee_budget(
		values, get_dimension_settings(), get_budget_rows_by_project([project] if project else [])
	)


def _match_employee_budget(emp, dimension_settings, budget_rows):
	employee_label = frappe.bold(f"{emp.name} - {emp.employee_name}")
	project = emp.get(EMPLOYEE_PROJECT_FIELD)

	if not project:
		return None, _("Employee {0}: Project is not set.").format(employee_label)

	dimensions = dimension_settings.get(project)
	if dimensions is None:
		return None, _("Employee {0}: Project {1} is not configured in {2}.").format(
			employee_label, frappe.bold(project), SETTINGS_DOCTYPE
		)

	missing = [d for d in dimensions if not emp.get(PAYROLL_DIMENSIONS[d]["employee_field"])]
	if missing:
		return None, _("Employee {0}: missing {1} required by Project {2}.").format(
			employee_label, frappe.bold(", ".join(missing)), frappe.bold(project)
		)

	project_rows = budget_rows.get(project)
	if not project_rows:
		return None, _("Employee {0}: no {1} exists for Project {2}.").format(
			employee_label, BUDGET_DOCTYPE, frappe.bold(project)
		)

	key = get_dimension_key(emp, dimensions, "employee_field")
	matches = [r for r in project_rows if get_dimension_key(r, dimensions, "budget_field") == key]

	required = (
		", ".join(f"{d} = {v}" for d, v in zip(dimensions, key)) if dimensions else _("Project only")
	)
	if not matches:
		return None, _(
			"Employee {0}: no budget configuration in {1} {2} for dimensions [{3}]."
		).format(employee_label, BUDGET_DOCTYPE, frappe.bold(project), required)
	if len(matches) > 1:
		return None, _(
			"Employee {0}: rows {1} of {2} {3} all match dimensions [{4}]. Re-save the budget to remove duplicates."
		).format(
			employee_label,
			", ".join(str(r.idx) for r in matches),
			BUDGET_DOCTYPE,
			frappe.bold(project),
			required,
		)

	return matches[0], None
