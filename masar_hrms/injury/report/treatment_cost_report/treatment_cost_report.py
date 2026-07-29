import frappe
from frappe.utils import cint, flt

from masar_hrms.injury.doctype.work_injury_settings.work_injury_settings import get_settings


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		"Injury No:Link/Work Injury:130",
		"Employee:Link/Employee:120",
		"Employee Name:Data:150",
		"Department:Link/Department:150",
		"Company:Link/Company:150",
		"Hospital:Data:150",
		"Cost:Currency:100",
		"Total Case Cost:Currency:130",
		"Limit Exceeded:Data:110",
	]


def get_data(filters):
	filters = filters or {}
	settings = get_settings()
	conditions, values = get_conditions(filters)

	rows = frappe.db.sql(
		f"""
		select wi.name, wi.employee, e.employee_name, wi.department, wi.company,
			wid.institution_name, wid.cost_of_treatment, wi.total_cost_of_treatment
		from `tabWork Injury` wi
		inner join `tabWork Injury Detail` wid on wid.parent = wi.name
		left join `tabEmployee` e on e.name = wi.employee
		where wi.docstatus = 1 {conditions}
		order by wi.name
		""",
		values,
	)

	limit_enabled = cint(settings.cost_limit)
	limit_value = flt(settings.treatment_cost_limit)

	data = []
	for (
		name,
		employee,
		employee_name,
		department,
		company,
		institution_name,
		cost_of_treatment,
		total_cost_of_treatment,
	) in rows:
		limit_exceeded = "-"
		if limit_enabled:
			limit_exceeded = "Yes" if flt(total_cost_of_treatment) > limit_value else "No"

		data.append(
			(
				name,
				employee,
				employee_name,
				department,
				company,
				institution_name,
				cost_of_treatment,
				total_cost_of_treatment,
				limit_exceeded,
			)
		)

	return data


def get_conditions(filters):
	conditions = ""
	values = {}

	if filters.get("company"):
		conditions += " and wi.company = %(company)s"
		values["company"] = filters["company"]

	if filters.get("department"):
		conditions += " and wi.department = %(department)s"
		values["department"] = filters["department"]

	if filters.get("employee"):
		conditions += " and wi.employee = %(employee)s"
		values["employee"] = filters["employee"]

	return conditions, values
