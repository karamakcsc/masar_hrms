# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_data(filters):
    _from, to = filters.get('from'), filters.get('to')  # date range

    # Conditions
    conditions = " AND 1=1 "
    if filters.get('company'):
        conditions += f" AND tss.company='{filters.get('company')}' "
    if filters.get('work_type'):
        conditions += f" AND tss.work_type='{filters.get('work_type')}' "
    if filters.get('branch'):
        conditions += f" AND tss.branch LIKE '%{filters.get('branch')}' "
    if filters.get('dep'):
        conditions += f" AND tss.department LIKE '%{filters.get('dep')}' "

    components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])
    earnings = sorted([c.name for c in components if c.type == "Earning"])
    deductions = sorted([c.name for c in components if c.type == "Deduction"])
    base_comp = frappe.get_value("Company", filters.get('company'), "custom_basic_salary_component")

    # frappe.throw(str(base_comp))  # <- fixed indentation here

    earnings_set = set()
    basic_sql = ""
    for comp in earnings:
        if comp == base_comp:
            basic_sql = f"SUM(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"
            earnings_set.add(comp)

    earning_comps = ""
    for comp in earnings:
        if comp not in earnings_set:
            earning_comps += f"SUM(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"

    deductions_set = set()
    ss_sql = ""
    for comp in deductions:
        if comp == "Social Security":
            ss_sql = f"SUM(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"
            deductions_set.add(comp)

    deduction_comps = ""
    for comp in deductions:
        if comp not in deductions_set:
            deduction_comps += f"SUM(CASE WHEN tsd.salary_component = '{comp}' THEN tsd.amount END) AS `{comp}`,\n"

    # SQL Query
    data = frappe.db.sql(f"""
        WITH base_amounts AS (
            SELECT
                DATE_FORMAT(tss.start_date, '%Y-%m') AS month,
                tss.work_type,
                tss.company,
                SUM(tss.gross_pay) AS total_gross_pay,
                SUM(tss.total_deduction) AS total_deductions,
                SUM(tss.net_pay) AS total_net_pay,
                tss.employee AS emp,
                SUM(
                    CASE 
                        WHEN tss.payment_days < 16 THEN 0
                        ELSE 
                            CASE 
                                WHEN te.custom_is_hazard = 1 THEN IFNULL(te.social_security_salary, 0) * 0.15250 
                                ELSE IFNULL(te.social_security_salary, 0) * 0.14250 
                            END
                    END
                ) AS `ss_company`
            FROM `tabSalary Slip` tss
            INNER JOIN `tabEmployee` te ON te.name = tss.employee
            WHERE tss.docstatus = 1 
            AND (tss.start_date BETWEEN '{_from}' AND '{to}') {conditions}
            GROUP BY DATE_FORMAT(tss.start_date, '%Y-%m'), tss.work_type, tss.company
        )
        SELECT 
            ba.month AS `Month`,
            ba.work_type AS `Work Type`,
            ba.company AS `Company`,
            ba.total_gross_pay AS `Reserved Salary`,
            {basic_sql}
            {earning_comps}
            ba.total_gross_pay AS `Total Earnings`,
            {ss_sql}
            ba.ss_company AS `Social Security Company Share`,
            {deduction_comps}
            ba.total_deductions AS `Total Deductions`,
            ba.total_net_pay AS `Net Pay`
        FROM base_amounts ba
        LEFT JOIN `tabSalary Slip` tss ON DATE_FORMAT(tss.start_date, '%Y-%m') = ba.month 
            AND tss.work_type = ba.work_type 
            AND tss.company = ba.company
            AND tss.docstatus = 1
        LEFT JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent
        WHERE (tss.start_date BETWEEN '{_from}' AND '{to}') {conditions}
        GROUP BY ba.month, ba.work_type, ba.company
        ORDER BY ba.month ASC
    """)

    return data

def get_columns():
    columns = [
        "Month: Date:200",
        "Work Type: Data:200",
        "Company: Data:300",
        "Reserved Salary: Currency:150",
    ]

    components = frappe.get_all("Salary Component", filters={"disabled": 0}, fields=["name", "type"])

    earnings = sorted([c.name for c in components if c.type == "Earning"])
    deductions = sorted([c.name for c in components if c.type == "Deduction"])

    earnings_set = set()
    for comp in earnings:
        if comp == "Basic":
            columns.append(f"{comp}:Currency:150")
            earnings_set.add(comp)

    for comp in earnings:
        if comp not in earnings_set:
            columns.append(f"{comp}:Currency:150")

    columns += ["Total Earnings: Currency:150"]

    deductions_set = set()
    for comp in deductions:
        if comp == "Social Security":
            columns.append(f"{comp}:Currency:150")
            deductions_set.add(comp)
    columns += [
        "Social Security Company Share: Currency:175",
    ]
    for comp in deductions:
        if comp not in deductions_set:
            columns.append(f"{comp}:Currency:150")

    columns += [
        "Total Deductions: Currency:150",
        "Net Pay: Currency:150",
    ]

    return columns
