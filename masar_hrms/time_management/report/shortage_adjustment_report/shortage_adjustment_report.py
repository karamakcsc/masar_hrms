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
            "fieldname": "calculated_shortage",
            "label":     _("Calculated Shortage (hrs)"),
            "fieldtype": "Float",
            "width":     140,
        },
        {
            "fieldname": "approved_shortage_col",
            "label":     _("Approved Shortage (hrs)"),
            "fieldtype": "Float",
            "width":     140,
        },
        {
            "fieldname": "difference",
            "label":     _("Difference (hrs)"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "approved_amount",
            "label":     _("Deduction Amount"),
            "fieldtype": "Currency",
            "width":     130,
        },
        {
            "fieldname": "modified_by",
            "label":     _("Modified By"),
            "fieldtype": "Data",
            "width":     150,
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
            eld.attendance_date,
            ROUND(COALESCE(eld.total_shortage, 0) / 3600, 2)                AS calculated_shortage,
            ROUND(COALESCE(eld.approved_shortage, 0) / 3600, 2)             AS approved_shortage_col,
            ROUND(
                (COALESCE(eld.total_shortage, 0) - COALESCE(eld.approved_shortage, 0)) / 3600,
                2
            )                                                                AS difference,
            ROUND(COALESCE(eld.amount, 0), 3)                               AS approved_amount,
            eap.modified_by
        FROM `tabEAP Leave Detail` eld
        JOIN `tabEmployee Attendance Process` eap ON eap.name = eld.parent
        JOIN `tabEmployee` emp ON emp.name = eap.employee
        WHERE eap.docstatus = 1
          AND eld.total_shortage != eld.approved_shortage
          AND {conditions}
        ORDER BY eld.attendance_date, eap.employee
        """,
        filters,
        as_dict=1,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_conditions(filters):
    parts = ["eld.attendance_date BETWEEN %(from_date)s AND %(to_date)s"]
    if filters.get("employee"):
        parts.append("eap.employee = %(employee)s")
    if filters.get("department"):
        parts.append("emp.department = %(department)s")
    return " AND ".join(parts)
