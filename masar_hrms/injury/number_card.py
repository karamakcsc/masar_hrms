import frappe
from frappe.utils import today


def _case_names_by_end_date(operator):
	return frappe.db.sql_list(
		f"""
		select wi.name
		from `tabWork Injury` wi
		inner join `tabWork Injury Detail` wid on wid.parent = wi.name
		where wi.docstatus = 1
		group by wi.name
		having max(wid.end_date) {operator} %(today)s
		""",
		{"today": today()},
	)


@frappe.whitelist()
def get_open_cases_count():
	return len(_case_names_by_end_date(">="))


@frappe.whitelist()
def get_employees_under_treatment_count():
	names = _case_names_by_end_date(">=")
	if not names:
		return 0
	employees = frappe.get_all("Work Injury", filters={"name": ["in", names]}, pluck="employee")
	return len(set(employees))


@frappe.whitelist()
def get_closed_cases_this_year_count():
	return frappe.db.sql(
		"""
		select count(*) from (
			select wi.name
			from `tabWork Injury` wi
			inner join `tabWork Injury Detail` wid on wid.parent = wi.name
			where wi.docstatus = 1
			group by wi.name
			having max(wid.end_date) < %(today)s and year(max(wid.end_date)) = year(%(today)s)
		) closed_cases
		""",
		{"today": today()},
	)[0][0]
