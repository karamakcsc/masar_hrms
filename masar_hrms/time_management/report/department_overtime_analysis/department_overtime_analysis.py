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
            "fieldname": "department",
            "label":     _("Department"),
            "fieldtype": "Link",
            "options":   "Department",
            "width":     160,
        },
        {
            "fieldname": "employee_count",
            "label":     _("Employee Count"),
            "fieldtype": "Int",
            "width":     120,
        },
        {
            "fieldname": "calculated_hours",
            "label":     _("Total Calculated OT (hrs)"),
            "fieldtype": "Float",
            "width":     140,
        },
        {
            "fieldname": "approved_hours",
            "label":     _("Total Approved OT (hrs)"),
            "fieldtype": "Float",
            "width":     140,
        },
        {
            "fieldname": "rejected_hours",
            "label":     _("Total Rejected OT (hrs)"),
            "fieldtype": "Float",
            "width":     140,
        },
        {
            "fieldname": "approved_cost",
            "label":     _("Approved OT Cost"),
            "fieldtype": "Currency",
            "width":     140,
        },
        {
            "fieldname": "cost_saved",
            "label":     _("Cost Saved"),
            "fieldtype": "Currency",
            "width":     140,
        },
        {
            "fieldname": "approval_rate",
            "label":     _("Approval Rate %"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "avg_ot_per_emp",
            "label":     _("Avg OT/Employee (hrs)"),
            "fieldtype": "Float",
            "width":     130,
        },
    ]


# ─── Data ─────────────────────────────────────────────────────────────────────

def get_data(filters):
    return frappe.db.sql(
        """
        SELECT
            emp.department,
            COUNT(DISTINCT eap.employee)                                      AS employee_count,
            ROUND(
                SUM(COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0)) / 3600,
                2
            )                                                                 AS calculated_hours,
            ROUND(
                SUM(COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0)) / 3600,
                2
            )                                                                 AS approved_hours,
            ROUND(
                SUM(
                    (COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0))
                    - (COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0))
                ) / 3600,
                2
            )                                                                 AS rejected_hours,
            ROUND(
                SUM(COALESCE(eap.ot_wd_amount, 0) + COALESCE(eap.ot_od_amount, 0)),
                3
            )                                                                 AS approved_cost,
            ROUND(
                SUM(
                    (COALESCE(eap.actual_ot_wd_amount, 0) + COALESCE(eap.actual_ot_od_amount, 0))
                    - (COALESCE(eap.ot_wd_amount, 0) + COALESCE(eap.ot_od_amount, 0))
                ),
                3
            )                                                                 AS cost_saved,
            CASE
                WHEN SUM(COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0)) > 0
                THEN ROUND(
                    SUM(COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0))
                    / SUM(COALESCE(eap.actual_ot_wd_time, 0) + COALESCE(eap.actual_ot_od_time, 0))
                    * 100,
                    2
                )
                ELSE 0
            END                                                               AS approval_rate,
            CASE
                WHEN COUNT(DISTINCT eap.employee) > 0
                THEN ROUND(
                    SUM(COALESCE(eap.ot_wd_time, 0) + COALESCE(eap.ot_od_time, 0)) / 3600
                    / COUNT(DISTINCT eap.employee),
                    2
                )
                ELSE 0
            END                                                               AS avg_ot_per_emp
        FROM `tabEmployee Attendance Process` eap
        JOIN `tabEmployee` emp ON emp.name = eap.employee
        WHERE eap.docstatus = 1
          AND eap.from_date >= %(from_date)s
          AND eap.to_date   <= %(to_date)s
        GROUP BY emp.department
        ORDER BY approved_cost DESC
        """,
        filters,
        as_dict=1,
    )
