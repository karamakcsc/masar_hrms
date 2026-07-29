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
            "fieldname": "calculated_hours",
            "label":     _("Calculated Off-Day OT (hrs)"),
            "fieldtype": "Float",
            "width":     130,
        },
        {
            "fieldname": "approved_hours",
            "label":     _("Approved Off-Day OT (hrs)"),
            "fieldtype": "Float",
            "width":     130,
        },
        {
            "fieldname": "rejected_hours",
            "label":     _("Rejected (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "approved_amount",
            "label":     _("Approved Amount"),
            "fieldtype": "Currency",
            "width":     130,
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
            ROUND(COALESCE(eod.calculated_overtime, 0) / 3600, 2)           AS calculated_hours,
            ROUND(COALESCE(eod.overtime, 0) / 3600, 2)                      AS approved_hours,
            ROUND(
                (COALESCE(eod.calculated_overtime, 0) - COALESCE(eod.overtime, 0)) / 3600,
                2
            )                                                                AS rejected_hours,
            ROUND(
                (COALESCE(eod.overtime, 0) / 3600)
                * COALESCE(eap.ot_od_rate, 0)
                * COALESCE(eap.basic_salary_hour_rate, 0),
                3
            )                                                                AS approved_amount
        FROM `tabEAP Overtime Detail` eod
        JOIN `tabEmployee Attendance Process` eap ON eap.name = eod.parent
        JOIN `tabEmployee` emp ON emp.name = eap.employee
        WHERE eap.docstatus = 1
          AND eod.off_day = 1
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
