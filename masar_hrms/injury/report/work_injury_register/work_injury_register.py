import frappe
from frappe.utils import date_diff, today

from masar_hrms.injury.utils import get_work_injury_status


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		"Injury No:Link/Work Injury:150",
		"Employee:Link/Employee:120",
		"Employee Name:Data:150",
		"Department:Link/Department:150",
		"Injury Date:Date:100",
		"Status:Data:110",
		"Total Days:Float:90",
		"Treatment Cost:Currency:120",
		"Case Age (Days):Int:120",
		"Payroll Status:Data:130",
	]


def get_data(filters):
	filters = filters or {}
	conditions, values = get_conditions(filters)

	rows = frappe.db.sql(
		f"""
		select
			wi.name, wi.employee, e.employee_name, wi.department,
			wi.injury_start_date, wi.docstatus, wi.total_days,
			wi.total_cost_of_treatment, wi.deduction_days, med.max_end_date
		from `tabWork Injury` wi
		left join `tabEmployee` e on e.name = wi.employee
		left join (
			select parent, max(end_date) as max_end_date
			from `tabWork Injury Detail`
			group by parent
		) med on med.parent = wi.name
		where 1=1 {conditions}
		order by wi.injury_start_date desc
		""",
		values,
	)

	status_filter = filters.get("status")
	data = []
	for (
		name,
		employee,
		employee_name,
		department,
		injury_start_date,
		docstatus,
		total_days,
		total_cost_of_treatment,
		deduction_days,
		max_end_date,
	) in rows:
		status = get_work_injury_status(docstatus, max_end_date)
		if status_filter and status != status_filter:
			continue

		case_age = date_diff(today(), injury_start_date) if injury_start_date else 0
		payroll_status = "Affects Payroll" if deduction_days and deduction_days > 0 else "No Impact"

		data.append(
			(
				name,
				employee,
				employee_name,
				department,
				injury_start_date,
				status,
				total_days,
				total_cost_of_treatment,
				case_age,
				payroll_status,
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

	if filters.get("from_date"):
		conditions += " and wi.injury_start_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " and wi.injury_start_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	return conditions, values
