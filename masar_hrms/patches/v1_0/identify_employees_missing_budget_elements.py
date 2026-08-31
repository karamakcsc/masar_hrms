import frappe


def execute():
	"""Employee Budget Element / Company Social Security Budget Element are now
	mandatory fields. This patch never assigns a value to any employee - it only
	surfaces which active employees are missing one or both fields so they can be
	fixed by hand before the mandatory-field validation (on save) and the Payroll
	Entry budgeting validation (on submit) start blocking them.

	The result is written to the Error Log (title "Employees Missing Budget
	Element") and printed to the migrate console.
	"""
	if not frappe.db.has_column("Employee", "custom_employee_budget_element"):
		return

	Employee = frappe.qb.DocType("Employee")
	missing = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name,
			Employee.employee_name,
			Employee.company,
			Employee.status,
			Employee.custom_employee_budget_element,
			Employee.custom_company_social_security_budget_element,
		)
		.where(
			(Employee.status != "Left")
			& (
				(Employee.custom_employee_budget_element.isnull())
				| (Employee.custom_employee_budget_element == "")
				| (Employee.custom_company_social_security_budget_element.isnull())
				| (Employee.custom_company_social_security_budget_element == "")
			)
		)
	).run(as_dict=True)

	if not missing:
		print("[masar_hrms] All active employees already have both Budget Element fields set.")
		return

	lines = []
	for emp in missing:
		gaps = []
		if not emp.custom_employee_budget_element:
			gaps.append("Employee Budget Element")
		if not emp.custom_company_social_security_budget_element:
			gaps.append("Company Social Security Budget Element")
		lines.append(f"{emp.name} - {emp.employee_name} ({emp.company}, {emp.status}): missing {', '.join(gaps)}")

	message = "\n".join(lines)
	print(f"[masar_hrms] {len(missing)} active employee(s) missing a required Budget Element:")
	print(message)

	frappe.log_error(
		title="Employees Missing Budget Element",
		message=(
			"The following active employees are missing Employee Budget Element and/or "
			"Company Social Security Budget Element. These fields are now mandatory; "
			"fix these records before running payroll for these employees.\n\n" + message
		),
	)
