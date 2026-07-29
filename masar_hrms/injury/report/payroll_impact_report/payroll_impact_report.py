import frappe
from frappe.utils import flt, formatdate

from masar_hrms.injury.doctype.work_injury_settings.work_injury_settings import get_settings


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		"Employee:Link/Employee:120",
		"Employee Name:Data:150",
		"Injury No:Link/Work Injury:150",
		"Payroll Month:Data:110",
		"Paid Days:Float:90",
		"Deduction Days:Float:100",
		"Daily Wage:Currency:110",
		"Deduction Amount:Currency:130",
	]


def get_data(filters):
	filters = filters or {}
	settings = get_settings()
	if not settings.injury_deduction_component:
		return []

	conditions, values = get_conditions(filters)
	values["component"] = settings.injury_deduction_component

	slip_names = frappe.db.sql_list(
		f"""
		select distinct sd.parent
		from `tabSalary Detail` sd
		inner join `tabSalary Slip` ss on ss.name = sd.parent
		where sd.parentfield = 'deductions'
			and sd.salary_component = %(component)s
			and sd.amount > 0
			and ss.docstatus = 1
			{conditions}
		""",
		values,
	)

	data = []
	for slip_name in slip_names:
		data.extend(get_rows_for_slip(slip_name, settings, filters))

	return data


def get_rows_for_slip(slip_name, settings, filters):
	slip = frappe.get_doc("Salary Slip", slip_name)
	deduction_row = next(
		(r for r in slip.deductions if r.salary_component == settings.injury_deduction_component), None
	)
	if not deduction_row or not flt(deduction_row.amount):
		return []

	attendance_rows = frappe.db.sql(
		"""
		select att.attendance_date, la.custom_work_injury_ref as work_injury
		from `tabAttendance` att
		inner join `tabLeave Application` la on la.name = att.leave_application
		where att.employee = %(employee)s
			and att.status = 'Injured'
			and att.docstatus = 1
			and att.attendance_date between %(start)s and %(end)s
			and la.custom_work_injury_ref is not null
		""",
		{"employee": slip.employee, "start": slip.start_date, "end": slip.actual_end_date},
		as_dict=True,
	)
	if not attendance_rows:
		return []

	days_by_case = {}
	for row in attendance_rows:
		days_by_case[row.work_injury] = days_by_case.get(row.work_injury, 0) + 1

	total_injured_days = sum(days_by_case.values())
	daily_rate = slip.get_work_injury_daily_rate(settings)

	total_deduction_days = 0
	if daily_rate and settings.ss_percent_ded:
		total_deduction_days = flt(deduction_row.amount) / (daily_rate * flt(settings.ss_percent_ded) / 100)

	payroll_month = formatdate(slip.start_date, "MMMM yyyy")

	rows = []
	for work_injury, injured_days in days_by_case.items():
		if filters.get("work_injury") and work_injury != filters["work_injury"]:
			continue

		share = injured_days / total_injured_days if total_injured_days else 0
		case_deduction_days = flt(total_deduction_days * share, 2)
		case_deduction_amount = flt(flt(deduction_row.amount) * share, 2)
		case_paid_days = max(0, injured_days - case_deduction_days)

		rows.append(
			(
				slip.employee,
				slip.employee_name,
				work_injury,
				payroll_month,
				case_paid_days,
				case_deduction_days,
				flt(daily_rate, 2),
				case_deduction_amount,
			)
		)

	return rows


def get_conditions(filters):
	conditions = ""
	values = {}

	if filters.get("employee"):
		conditions += " and ss.employee = %(employee)s"
		values["employee"] = filters["employee"]

	if filters.get("company"):
		conditions += " and ss.company = %(company)s"
		values["company"] = filters["company"]

	return conditions, values
