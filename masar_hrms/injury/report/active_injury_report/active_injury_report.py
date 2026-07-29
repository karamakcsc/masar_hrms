import frappe
from frappe.utils import date_diff, getdate, today


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		"Injury No:Link/Work Injury:150",
		"Employee:Link/Employee:120",
		"Employee Name:Data:150",
		"Remaining Days:Int:110",
		"Current Medical Period:Data:220",
		"Next Review Date:Date:120",
	]


def get_data(filters):
	filters = filters or {}
	conditions = "wi.docstatus = 1"
	values = {}

	if filters.get("employee"):
		conditions += " and wi.employee = %(employee)s"
		values["employee"] = filters["employee"]

	if filters.get("company"):
		conditions += " and wi.company = %(company)s"
		values["company"] = filters["company"]

	cases = frappe.db.sql(
		f"""
		select wi.name, wi.employee, e.employee_name
		from `tabWork Injury` wi
		left join `tabEmployee` e on e.name = wi.employee
		where {conditions}
		order by wi.injury_start_date desc
		""",
		values,
		as_dict=True,
	)

	data = []
	for case in cases:
		rows = frappe.get_all(
			"Work Injury Detail",
			filters={"parent": case.name},
			fields=["start_date", "end_date"],
			order_by="start_date asc",
		)
		if not rows:
			continue

		end_dates = [r.end_date for r in rows if r.end_date]
		if not end_dates:
			continue

		max_end_date = max(end_dates)
		if getdate(max_end_date) < getdate(today()):
			continue  # already closed - not an active case

		current_row = next(
			(
				r
				for r in rows
				if r.start_date and r.end_date and getdate(r.start_date) <= getdate(today()) <= getdate(r.end_date)
			),
			rows[-1],
		)

		data.append(
			(
				case.name,
				case.employee,
				case.employee_name,
				date_diff(max_end_date, today()),
				f"{current_row.start_date} to {current_row.end_date}",
				current_row.end_date,
			)
		)

	return data
