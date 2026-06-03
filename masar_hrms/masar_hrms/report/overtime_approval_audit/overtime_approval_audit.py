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
            "fieldname": "attendance_date",
            "label":     _("Attendance Date"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "ot_type",
            "label":     _("Type"),
            "fieldtype": "Data",
            "width":     120,
        },
        {
            "fieldname": "calculated_hours",
            "label":     _("Calculated OT (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "approved_hours",
            "label":     _("Approved OT (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "rejected_hours",
            "label":     _("Rejected OT (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "rejection_pct",
            "label":     _("Rejection %"),
            "fieldtype": "Float",
            "width":     100,
        },
        {
            "fieldname": "eap_reference",
            "label":     _("EAP Reference"),
            "fieldtype": "Link",
            "options":   "Employee Attendance Process",
            "width":     180,
        },
    ]


# ─── Data ─────────────────────────────────────────────────────────────────────

def get_data(filters):
    conditions = _build_conditions(filters)
    return frappe.db.sql(
        f"""
        SELECT
            eap.employee,
            emp.employee_name,
            emp.department,
            eod.attendance_date,
            CASE WHEN eod.off_day = 1 THEN 'Off Day' ELSE 'Working Day' END AS ot_type,
            ROUND(COALESCE(eod.calculated_overtime, 0) / 3600, 2)           AS calculated_hours,
            ROUND(COALESCE(eod.overtime, 0) / 3600, 2)                      AS approved_hours,
            ROUND(
                (COALESCE(eod.calculated_overtime, 0) - COALESCE(eod.overtime, 0)) / 3600,
                2
            )                                                                AS rejected_hours,
            CASE
                WHEN COALESCE(eod.calculated_overtime, 0) > 0
                THEN ROUND(
                    (COALESCE(eod.calculated_overtime, 0) - COALESCE(eod.overtime, 0))
                    / COALESCE(eod.calculated_overtime, 0) * 100,
                    2
                )
                ELSE 0
            END                                                              AS rejection_pct,
            eap.name                                                         AS eap_reference
        FROM `tabEmployee Attendance Process` eap
        JOIN `tabEAP Overtime Detail` eod ON eap.name = eod.parent
        JOIN `tabEmployee` emp ON emp.name = eap.employee
        WHERE eap.docstatus = 1
          AND {conditions}
        ORDER BY eod.attendance_date, eap.employee
        """,
        filters,
        as_dict=1,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_conditions(filters):
    parts = ["eod.attendance_date BETWEEN %(from_date)s AND %(to_date)s"]
    if filters.get("employee"):
        parts.append("eap.employee = %(employee)s")
    if filters.get("department"):
        parts.append("emp.department = %(department)s")
    return " AND ".join(parts)
