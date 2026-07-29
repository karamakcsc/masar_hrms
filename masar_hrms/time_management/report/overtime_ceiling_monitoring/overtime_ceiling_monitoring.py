import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data    = get_data(filters)
    return columns, data


# ─── Columns ──────────────────────────────────────────────────────────────────

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label":     _("Employee"),
            "fieldtype": "Link",
            "options":   "Employee",
            "width":     130,
        },
        {
            "fieldname": "employee_name",
            "label":     _("Employee Name"),
            "fieldtype": "Data",
            "width":     160,
        },
        {
            "fieldname": "department",
            "label":     _("Department"),
            "fieldtype": "Link",
            "options":   "Department",
            "width":     130,
        },
        {
            "fieldname": "from_date",
            "label":     _("Period From"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "to_date",
            "label":     _("Period To"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "wd_ceiling",
            "label":     _("WD Ceiling (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "wd_approved",
            "label":     _("WD Approved (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "wd_remaining",
            "label":     _("WD Remaining (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "wd_utilization",
            "label":     _("WD Utilization %"),
            "fieldtype": "Float",
            "width":     110,
        },
        {
            "fieldname": "od_ceiling",
            "label":     _("OD Ceiling (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "od_approved",
            "label":     _("OD Approved (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "od_remaining",
            "label":     _("OD Remaining (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "od_utilization",
            "label":     _("OD Utilization %"),
            "fieldtype": "Float",
            "width":     110,
        },
        {
            "fieldname": "indicator",
            "label":     _("Status"),
            "fieldtype": "Data",
            "width":     90,
        },
    ]


# ─── Data ─────────────────────────────────────────────────────────────────────

def get_data(filters):
    conditions = _build_conditions(filters)
    rows = frappe.db.sql(
        f"""
        SELECT
            eap.employee,
            emp.employee_name,
            emp.department,
            eap.from_date,
            eap.to_date,
            COALESCE(eap.ot_wd_ceiling, 0)                                   AS wd_ceiling,
            ROUND(COALESCE(eap.ot_wd_time, 0) / 3600, 2)                    AS wd_approved,
            CASE
                WHEN COALESCE(eap.ot_wd_ceiling, 0) > 0
                THEN ROUND(eap.ot_wd_ceiling - COALESCE(eap.ot_wd_time, 0) / 3600, 2)
                ELSE NULL
            END                                                               AS wd_remaining,
            CASE
                WHEN COALESCE(eap.ot_wd_ceiling, 0) > 0
                THEN ROUND(COALESCE(eap.ot_wd_time, 0) / 3600 / eap.ot_wd_ceiling * 100, 1)
                ELSE NULL
            END                                                               AS wd_utilization,
            COALESCE(eap.ot_od_ceiling, 0)                                   AS od_ceiling,
            ROUND(COALESCE(eap.ot_od_time, 0) / 3600, 2)                    AS od_approved,
            CASE
                WHEN COALESCE(eap.ot_od_ceiling, 0) > 0
                THEN ROUND(eap.ot_od_ceiling - COALESCE(eap.ot_od_time, 0) / 3600, 2)
                ELSE NULL
            END                                                               AS od_remaining,
            CASE
                WHEN COALESCE(eap.ot_od_ceiling, 0) > 0
                THEN ROUND(COALESCE(eap.ot_od_time, 0) / 3600 / eap.ot_od_ceiling * 100, 1)
                ELSE NULL
            END                                                               AS od_utilization
        FROM `tabEmployee Attendance Process` eap
        JOIN `tabEmployee` emp ON emp.name = eap.employee
        WHERE eap.docstatus = 1
          AND {conditions}
        ORDER BY wd_utilization DESC
        """,
        filters,
        as_dict=1,
    )

    # Add color indicator based on WD utilization
    for row in rows:
        wd_util = row.get("wd_utilization") or 0
        od_util = row.get("od_utilization") or 0
        max_util = max(wd_util, od_util)

        if max_util >= 95:
            row["indicator"] = "Red"
            row["_style"] = "color: #dc3545; font-weight: 600;"
        elif max_util >= 80:
            row["indicator"] = "Orange"
            row["_style"] = "color: #fd7e14; font-weight: 600;"
        else:
            row["indicator"] = "Green"
            row["_style"] = "color: #28a745;"

    return rows


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_conditions(filters):
    parts = [
        "eap.from_date >= %(from_date)s",
        "eap.to_date <= %(to_date)s",
    ]
    if filters.get("employee"):
        parts.append("eap.employee = %(employee)s")
    if filters.get("department"):
        parts.append("emp.department = %(department)s")
    return " AND ".join(parts)
