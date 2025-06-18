# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    _from, to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
    if filters.get('year'):
        conditions += f" AND YEAR(tss.posting_date) = '{filters.get('year')}'"
    if filters.get('month'):
        conditions += f" AND MONTH(tss.posting_date) = '{filters.get('month')}'"
    if _from and to:
        conditions += f" AND tss.posting_date BETWEEN '{_from}' AND '{to}'"
    
    sql = frappe.db.sql(f"""
        WITH current_month AS (
            SELECT 
                tss.employee,
                tss.name,
                tss.posting_date,
                tss.payment_days,
                tss.total_working_days,
                CASE WHEN tsd.parent IS NULL THEN 0 ELSE 1 END as has_social_security
            FROM `tabSalary Slip` tss
            LEFT JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent 
                AND tsd.salary_component = 'Social Security'
            WHERE tss.docstatus = 1 
            AND {conditions}
        ),
        prev_month_data AS (
            SELECT 
                cm.employee,
                cm.name as current_slip,
                cm.posting_date,
                cm.payment_days,
                cm.total_working_days,
                cm.has_social_security,
                prev.name as prev_slip,
                prev.payment_days as prev_payment_days,
                CASE WHEN prev_ss.parent IS NULL THEN 0 ELSE 1 END as prev_has_ss
            FROM current_month cm
            LEFT JOIN `tabSalary Slip` prev ON prev.employee = cm.employee 
                AND prev.posting_date = LAST_DAY(DATE_SUB(cm.posting_date, INTERVAL 1 MONTH))
                AND prev.docstatus = 1
            LEFT JOIN `tabSalary Detail` prev_ss ON prev.name = prev_ss.parent
                AND prev_ss.salary_component = 'Social Security'
        )
        SELECT
            te.name AS `Employee Number`,
            te.employee_name AS `Employee Name`,
            CASE
                WHEN te.nationality <> 'Jordan' THEN te.personal_no
                ELSE te.national_no
            END AS `National No`,
            te.custom_id_card_no AS `ID Card No`,
            te.date_of_birth AS `Date Of Birth`,
            te.date_of_joining AS `Date Of Joining`,
            te.social_security_number AS `Social Security Number`,
            te.social_security_salary AS `Social Security Salary`,
            pmd.total_working_days AS `Working Days`,
            pmd.payment_days AS `Payment Days`,
            tc.custom_establishment_number AS `Establishment No`,
            te.designation AS `Designation`,
            CASE
                WHEN te.custom_is_hazard = 1 THEN td.hazard_code
                ELSE ""
            END AS `Hazard Code`
        FROM tabEmployee te
        INNER JOIN prev_month_data pmd ON pmd.employee = te.name
        INNER JOIN `tabCompany` tc ON te.company = tc.name
        INNER JOIN `tabDesignation` td ON te.designation = td.name
        WHERE
            (pmd.payment_days < 16 OR pmd.has_social_security = 0)
            AND pmd.prev_slip IS NOT NULL
            AND pmd.prev_payment_days >= 16
            AND pmd.prev_has_ss = 1
        GROUP BY pmd.current_slip
        ORDER BY te.name;
    """)
    
    return sql

def get_columns():
    return[
        "Employee: Link/Employee:200",
        "Employee Name: Data:200",
        "National No/Personal No: Data:200",
        "ID Card No: Data:200",
        "Date of Birth: Date:200",
        "Date Of Joining: Data:200",
        "Social Security No: Data:200",
        "Social Security Salary: Data:200",
        "Working Days: Data:200",
        "Payment Days: Data:200",
        "Establishment No: Data:200",
        "Designation: Data:200",
        "Hazard Code: Data:200",
    ]