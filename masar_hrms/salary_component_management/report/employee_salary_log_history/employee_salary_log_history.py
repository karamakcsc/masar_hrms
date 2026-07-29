import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data    = get_data(filters)
    summary = get_summary(filters)
    chart   = get_chart(filters)
    return columns, data, None, chart, summary


# ─── Columns ──────────────────────────────────────────────────────────────────

def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label":     _("Posting Date"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "employee",
            "label":     _("Employee"),
            "fieldtype": "Link",
            "options":   "Employee",
            "width":     120,
        },
        {
            "fieldname": "employee_name",
            "label":     _("Employee Name"),
            "fieldtype": "Data",
            "width":     180,
        },
        {
            "fieldname": "department",
            "label":     _("Department"),
            "fieldtype": "Link",
            "options":   "Department",
            "width":     150,
        },
        {
            "fieldname": "salary_component",
            "label":     _("Salary Component"),
            "fieldtype": "Link",
            "options":   "Salary Component",
            "width":     160,
        },
        {
            "fieldname": "component_type",
            "label":     _("Type"),
            "fieldtype": "Data",
            "width":     90,
        },
        {
            "fieldname": "change_type",
            "label":     _("Change Type"),
            "fieldtype": "Data",
            "width":     100,
        },
        {
            "fieldname": "amount",
            "label":     _("Amount"),
            "fieldtype": "Float",
            "width":     120,
        },
        {
            "fieldname": "effective_date",
            "label":     _("Effective Date"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "is_active",
            "label":     _("Is Current"),
            "fieldtype": "Check",
            "width":     90,
        },
        {
            "fieldname": "voucher_type",
            "label":     _("Voucher Type"),
            "fieldtype": "Data",
            "width":     170,
        },
        {
            "fieldname": "voucher_no",
            "label":     _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options":   "voucher_type",
            "width":     180,
        },
        {
            "fieldname": "remarks",
            "label":     _("Remarks"),
            "fieldtype": "Small Text",
            "width":     200,
        },
    ]


# ─── Data ─────────────────────────────────────────────────────────────────────

def get_data(filters):
    conditions = _build_conditions(filters)
    return frappe.db.sql(
        f"""
        SELECT
            esl.posting_date,
            esl.employee,
            esl.employee_name,
            esl.department,
            esl.salary_component,
            esl.component_type,
            esl.change_type,
            esl.amount,
            esl.effective_date,
            esl.is_active,
            esl.voucher_type,
            esl.voucher_no,
            esl.remarks
        FROM `tabEmployee Salary Log` esl
        WHERE {conditions}
        ORDER BY esl.posting_date DESC, esl.employee, esl.salary_component
        """,
        filters,
        as_dict=1,
    )


# ─── KPI Summary ──────────────────────────────────────────────────────────────

def get_summary(filters):
    conditions = _build_conditions(filters)
    row = (
        frappe.db.sql(
            f"""
            SELECT
                COUNT(*)                           AS total,
                COUNT(DISTINCT esl.employee)       AS employees,
                SUM(esl.change_type = 'Added')     AS added,
                SUM(esl.change_type = 'Changed')   AS changed_count,
                SUM(esl.change_type = 'Removed')   AS removed,
                SUM(esl.is_active   = 1)           AS active
            FROM `tabEmployee Salary Log` esl
            WHERE {conditions}
            """,
            filters,
            as_dict=1,
        )
        or [{}]
    )[0]

    def val(key):
        return int(row.get(key) or 0)

    return [
        {
            "value":    val("total"),
            "label":    _("Total Transactions"),
            "datatype": "Int",
            "color":    "blue",
        },
        {
            "value":    val("employees"),
            "label":    _("Employees Affected"),
            "datatype": "Int",
            "color":    "purple",
        },
        {
            "value":    val("added"),
            "label":    _("Added"),
            "datatype": "Int",
            "color":    "green",
        },
        {
            "value":    val("changed_count"),
            "label":    _("Changed"),
            "datatype": "Int",
            "color":    "orange",
        },
        {
            "value":    val("removed"),
            "label":    _("Removed"),
            "datatype": "Int",
            "color":    "red",
        },
        {
            "value":    val("active"),
            "label":    _("Currently Active"),
            "datatype": "Int",
            "color":    "green",
        },
    ]


# ─── Chart ────────────────────────────────────────────────────────────────────

def get_chart(filters):
    conditions = _build_conditions(filters)
    rows = frappe.db.sql(
        f"""
        SELECT
            esl.change_type,
            COUNT(*) AS count
        FROM `tabEmployee Salary Log` esl
        WHERE {conditions}
        GROUP BY esl.change_type
        ORDER BY FIELD(esl.change_type, 'Added', 'Changed', 'Removed')
        """,
        filters,
        as_dict=1,
    )

    if not rows:
        return None

    labels  = [r.change_type for r in rows]
    values  = [r.count        for r in rows]
    colors  = []
    color_map = {"Added": "#28a745", "Changed": "#fd7e14", "Removed": "#dc3545"}
    for lbl in labels:
        colors.append(color_map.get(lbl, "#5e64ff"))

    return {
        "data": {
            "labels":   labels,
            "datasets": [{"name": _("Transactions"), "values": values}],
        },
        "type":   "donut",
        "colors": colors,
        "height": 280,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_conditions(filters):
    parts = ["1=1"]
    if filters.get("company"):
        parts.append("esl.company = %(company)s")
    if filters.get("employee"):
        parts.append("esl.employee = %(employee)s")
    if filters.get("department"):
        parts.append("esl.department = %(department)s")
    if filters.get("from_date"):
        parts.append("esl.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        parts.append("esl.posting_date <= %(to_date)s")
    if filters.get("change_type"):
        parts.append("esl.change_type = %(change_type)s")
    if filters.get("is_current"):
        parts.append("esl.is_active = 1")
    return " AND ".join(parts)
