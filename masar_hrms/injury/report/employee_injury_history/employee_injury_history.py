import frappe

from masar_hrms.injury.utils import get_work_injury_status


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		"Injury No:Link/Work Injury:150",
		"Injury Type:Data:170",
		"Injury Start Date:Date:120",
		"Status:Data:110",
		"Total Days:Float:90",
		"Treatment Cost:Currency:120",
		"Submitted On:Date:110",
	]


def get_data(filters):
	filters = filters or {}
	conditions = "1=1"
	values = {}

	if filters.get("employee"):
		conditions += " and wi.employee = %(employee)s"
		values["employee"] = filters["employee"]

	rows = frappe.db.sql(
		f"""
		select wi.name, wi.injury_type, wi.injury_start_date, wi.docstatus,
			wi.total_days, wi.total_cost_of_treatment, wi.posting_date, med.max_end_date
		from `tabWork Injury` wi
		left join (
			select parent, max(end_date) as max_end_date
			from `tabWork Injury Detail`
			group by parent
		) med on med.parent = wi.name
		where {conditions}
		order by wi.injury_start_date desc
		""",
		values,
	)

	data = []
	for (
		name,
		injury_type,
		injury_start_date,
		docstatus,
		total_days,
		total_cost_of_treatment,
		posting_date,
		max_end_date,
	) in rows:
		status = get_work_injury_status(docstatus, max_end_date)
		data.append((name, injury_type, injury_start_date, status, total_days, total_cost_of_treatment, posting_date))

	return data
