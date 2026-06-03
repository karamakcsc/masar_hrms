import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": "Status", "fieldname": "status",
			"fieldtype": "Data", "width": 90
		},
		{
			"label": "EAP Reference", "fieldname": "eap_name",
			"fieldtype": "Link", "options": "Employee Attendance Process", "width": 175
		},
		{
			"label": "Bulk Reference", "fieldname": "eapb_ref",
			"fieldtype": "Link", "options": "Employee Attendance Process Bulk", "width": 155
		},
		{
			"label": "Employee", "fieldname": "employee",
			"fieldtype": "Link", "options": "Employee", "width": 120
		},
		{
			"label": "Employee Name", "fieldname": "employee_name",
			"fieldtype": "Data", "width": 160
		},
		{
			"label": "Department", "fieldname": "department",
			"fieldtype": "Link", "options": "Department", "width": 140
		},
		{
			"label": "Designation", "fieldname": "designation",
			"fieldtype": "Link", "options": "Designation", "width": 140
		},
		{
			"label": "From Date", "fieldname": "from_date",
			"fieldtype": "Date", "width": 105
		},
		{
			"label": "To Date", "fieldname": "to_date",
			"fieldtype": "Date", "width": 105
		},
		{
			"label": "Posting Date", "fieldname": "posting_date",
			"fieldtype": "Date", "width": 110
		},
		{
			"label": "WD Ceiling (hrs)", "fieldname": "ot_wd_ceiling",
			"fieldtype": "Float", "width": 125, "precision": 2
		},
		{
			"label": "Actual WD OT (hrs)", "fieldname": "actual_ot_wd_hours",
			"fieldtype": "Float", "width": 145, "precision": 2
		},
		{
			"label": "Approved WD OT (hrs)", "fieldname": "approved_ot_wd_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "Rejected WD OT (hrs)", "fieldname": "rejected_ot_wd_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "WD Ceiling Util %", "fieldname": "wd_ceiling_utilization",
			"fieldtype": "Float", "width": 135, "precision": 1
		},
		{
			"label": "Actual WD OT Cost", "fieldname": "actual_ot_wd_amount",
			"fieldtype": "Currency", "width": 145
		},
		{
			"label": "Approved WD OT Cost", "fieldname": "approved_ot_wd_amount",
			"fieldtype": "Currency", "width": 155
		},
		{
			"label": "WD Cost Saved", "fieldname": "wd_ot_savings",
			"fieldtype": "Currency", "width": 125
		},
		{
			"label": "OD Ceiling (hrs)", "fieldname": "ot_od_ceiling",
			"fieldtype": "Float", "width": 125, "precision": 2
		},
		{
			"label": "Actual OD OT (hrs)", "fieldname": "actual_ot_od_hours",
			"fieldtype": "Float", "width": 145, "precision": 2
		},
		{
			"label": "Approved OD OT (hrs)", "fieldname": "approved_ot_od_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "Rejected OD OT (hrs)", "fieldname": "rejected_ot_od_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "OD Ceiling Util %", "fieldname": "od_ceiling_utilization",
			"fieldtype": "Float", "width": 135, "precision": 1
		},
		{
			"label": "Actual OD OT Cost", "fieldname": "actual_ot_od_amount",
			"fieldtype": "Currency", "width": 145
		},
		{
			"label": "Approved OD OT Cost", "fieldname": "approved_ot_od_amount",
			"fieldtype": "Currency", "width": 155
		},
		{
			"label": "OD Cost Saved", "fieldname": "od_ot_savings",
			"fieldtype": "Currency", "width": 125
		},
		{
			"label": "Total Actual OT (hrs)", "fieldname": "total_actual_ot_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "Total Approved OT (hrs)", "fieldname": "total_approved_ot_hours",
			"fieldtype": "Float", "width": 165, "precision": 2
		},
		{
			"label": "Total Actual OT Cost", "fieldname": "total_actual_ot_amount",
			"fieldtype": "Currency", "width": 155
		},
		{
			"label": "Total Approved OT Cost", "fieldname": "total_approved_ot_amount",
			"fieldtype": "Currency", "width": 165
		},
		{
			"label": "Total OT Savings", "fieldname": "total_ot_savings",
			"fieldtype": "Currency", "width": 135
		},
		{
			"label": "OT Approval Rate %", "fieldname": "ot_approval_rate",
			"fieldtype": "Float", "width": 145, "precision": 1
		},
		{
			"label": "Actual Shortage (hrs)", "fieldname": "actual_shortage_hours",
			"fieldtype": "Float", "width": 155, "precision": 2
		},
		{
			"label": "Approved Shortage (hrs)", "fieldname": "approved_shortage_hours",
			"fieldtype": "Float", "width": 165, "precision": 2
		},
		{
			"label": "Shortage Reduced (hrs)", "fieldname": "shortage_reduced_hours",
			"fieldtype": "Float", "width": 160, "precision": 2
		},
		{
			"label": "Actual Shortage Cost", "fieldname": "actual_shortage_amount",
			"fieldtype": "Currency", "width": 155
		},
		{
			"label": "Approved Shortage Cost", "fieldname": "approved_shortage_amount",
			"fieldtype": "Currency", "width": 165
		},
		{
			"label": "Shortage Savings", "fieldname": "shortage_savings",
			"fieldtype": "Currency", "width": 135
		},
		{
			"label": "Basic Salary", "fieldname": "basic_salary",
			"fieldtype": "Currency", "width": 125
		},
		{
			"label": "Earning Salary", "fieldname": "earning_salary",
			"fieldtype": "Currency", "width": 125
		},
		{
			"label": "OT Hour Rate", "fieldname": "hour_rate",
			"fieldtype": "Float", "width": 115, "precision": 3
		},
		{
			"label": "Shortage Hour Rate", "fieldname": "shortage_hour_rate",
			"fieldtype": "Float", "width": 145, "precision": 3
		},
	]


def get_data(filters):
	conditions, values = _build_conditions(filters)

	data = frappe.db.sql("""
		SELECT
			CASE WHEN eap.docstatus = 0 THEN 'Draft' ELSE 'Submitted' END AS status,
			eap.name  AS eap_name,
			eap.eapb_ref,

			eap.employee,
			eap.employee_name,
			COALESCE(emp.department, eap.department)    AS department,
			emp.designation,

			eap.from_date,
			eap.to_date,
			eap.posting_date,

			/* ── Working Day OT ── */
			COALESCE(eap.ot_wd_ceiling, 0)  AS ot_wd_ceiling,

			ROUND(COALESCE(eap.actual_ot_wd_time, 0) / 3600, 2)  AS actual_ot_wd_hours,
			ROUND(COALESCE(eap.ot_wd_time, 0) / 3600, 2)          AS approved_ot_wd_hours,
			ROUND((COALESCE(eap.actual_ot_wd_time, 0) - COALESCE(eap.ot_wd_time, 0)) / 3600, 2)
				AS rejected_ot_wd_hours,
			CASE WHEN COALESCE(eap.ot_wd_ceiling, 0) > 0
				THEN ROUND(COALESCE(eap.ot_wd_time, 0) / 3600 / eap.ot_wd_ceiling * 100, 1)
				ELSE NULL END  AS wd_ceiling_utilization,

			ROUND(COALESCE(eap.actual_ot_wd_amount, 0), 3)  AS actual_ot_wd_amount,
			ROUND(COALESCE(eap.ot_wd_amount, 0), 3)          AS approved_ot_wd_amount,
			ROUND(COALESCE(eap.actual_ot_wd_amount, 0) - COALESCE(eap.ot_wd_amount, 0), 3)
				AS wd_ot_savings,

			/* ── Off-Day OT ── */
			COALESCE(eap.ot_od_ceiling, 0)  AS ot_od_ceiling,

			ROUND(COALESCE(eap.actual_ot_od_time, 0) / 3600, 2)  AS actual_ot_od_hours,
			ROUND(COALESCE(eap.ot_od_time, 0) / 3600, 2)          AS approved_ot_od_hours,
			ROUND((COALESCE(eap.actual_ot_od_time, 0) - COALESCE(eap.ot_od_time, 0)) / 3600, 2)
				AS rejected_ot_od_hours,
			CASE WHEN COALESCE(eap.ot_od_ceiling, 0) > 0
				THEN ROUND(COALESCE(eap.ot_od_time, 0) / 3600 / eap.ot_od_ceiling * 100, 1)
				ELSE NULL END  AS od_ceiling_utilization,

			ROUND(COALESCE(eap.actual_ot_od_amount, 0), 3)  AS actual_ot_od_amount,
			ROUND(COALESCE(eap.ot_od_amount, 0), 3)          AS approved_ot_od_amount,
			ROUND(COALESCE(eap.actual_ot_od_amount, 0) - COALESCE(eap.ot_od_amount, 0), 3)
				AS od_ot_savings,

			/* ── OT Totals ── */
			ROUND((COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0)) / 3600, 2)
				AS total_actual_ot_hours,
			ROUND((COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0)) / 3600, 2)
				AS total_approved_ot_hours,

			ROUND(COALESCE(eap.actual_ot_wd_amount, 0) + COALESCE(eap.actual_ot_od_amount, 0), 3)
				AS total_actual_ot_amount,
			ROUND(COALESCE(eap.total_amount, 0), 3)   AS total_approved_ot_amount,
			ROUND((COALESCE(eap.actual_ot_wd_amount, 0) + COALESCE(eap.actual_ot_od_amount, 0))
				- COALESCE(eap.total_amount, 0), 3)   AS total_ot_savings,

			CASE WHEN (COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0)) > 0
				THEN ROUND(
					(COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0))
					/ (COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0)) * 100,
				1)
				ELSE NULL END  AS ot_approval_rate,

			/* ── Shortage ── */
			ROUND(COALESCE(eap.actual_total_shortage, 0) / 3600, 2)   AS actual_shortage_hours,
			ROUND(COALESCE(eap.total_shortage, 0) / 3600, 2)           AS approved_shortage_hours,
			ROUND((COALESCE(eap.actual_total_shortage, 0) - COALESCE(eap.total_shortage, 0)) / 3600, 2)
				AS shortage_reduced_hours,

			ROUND(COALESCE(eap.actual_total_shortage_amount, 0), 3)   AS actual_shortage_amount,
			ROUND(COALESCE(eap.total_shortage_amount, 0), 3)           AS approved_shortage_amount,
			ROUND(COALESCE(eap.actual_total_shortage_amount, 0)
				- COALESCE(eap.total_shortage_amount, 0), 3)           AS shortage_savings,

			/* ── Salary ── */
			ROUND(COALESCE(eap.basic_salary, 0), 3)           AS basic_salary,
			ROUND(COALESCE(eap.earning_salary, 0), 3)         AS earning_salary,
			ROUND(COALESCE(eap.basic_salary_hour_rate, 0), 3) AS hour_rate,
			ROUND(COALESCE(eap.shortage_hour_rate, 0), 3)     AS shortage_hour_rate

		FROM `tabEmployee Attendance Process` eap
		INNER JOIN `tabEmployee` emp ON emp.name = eap.employee
		WHERE {conditions}
		ORDER BY eap.from_date ASC, eap.employee ASC
	""".format(conditions=conditions), values, as_dict=True)
	for row in data:
		wd_util = flt(row.get('wd_ceiling_utilization') or 0)
		od_util = flt(row.get('od_ceiling_utilization') or 0)
		max_util = max(wd_util, od_util)
		if max_util >= 95:
			row['_color'] = 'red'
		elif max_util >= 80:
			row['_color'] = 'orange'
	return data

def _build_conditions(filters):
	values = {}
	conds = []
	if filters.get('trial'):
		conds.append("eap.docstatus IN (0, 1)")
	else:
		conds.append("eap.docstatus = 1")
	if filters.get('from_date'):
		conds.append("eap.from_date >= %(from_date)s")
		values['from_date'] = filters['from_date']

	if filters.get('to_date'):
		conds.append("eap.to_date <= %(to_date)s")
		values['to_date'] = filters['to_date']
	if filters.get('employee'):
		conds.append("eap.employee = %(employee)s")
		values['employee'] = filters['employee']
	if filters.get('department'):
		conds.append("emp.department = %(department)s")
		values['department'] = filters['department']
	if filters.get('designation'):
		conds.append("emp.designation = %(designation)s")
		values['designation'] = filters['designation']
	if filters.get('eapb_ref'):
		conds.append("eap.eapb_ref = %(eapb_ref)s")
		values['eapb_ref'] = filters['eapb_ref']
	work_type = filters.get('work_type')
	if work_type == 'Working Day Only':
		conds.append("""(
			COALESCE(eap.actual_ot_wd_time, 0) > 0
			OR COALESCE(eap.ot_wd_time, 0) > 0
		)""")
	elif work_type == 'Off Day Only':
		conds.append("""(
			COALESCE(eap.actual_ot_od_time, 0) > 0
			OR COALESCE(eap.ot_od_time, 0) > 0
		)""")
	elif work_type == 'Has Shortage':
		conds.append("COALESCE(eap.actual_total_shortage, 0) > 0")
	elif work_type == 'Has OT':
		conds.append("""(
			COALESCE(eap.actual_ot_wd_time, 0) > 0
			OR COALESCE(eap.actual_ot_od_time, 0) > 0
		)""")
	elif work_type == 'Has Rejection':
		conds.append("""(
			COALESCE(eap.actual_ot_wd_time, 0) > COALESCE(eap.ot_wd_time, 0)
			OR COALESCE(eap.actual_ot_od_time, 0) > COALESCE(eap.ot_od_time, 0)
		)""")

	return " AND ".join(conds) if conds else "1=1", values
