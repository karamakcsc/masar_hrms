# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return get_columns(filters), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND te.name = '{filters.get('employee')}'"
    if filters.get('year'):
        conditions += f" AND YEAR(tss.posting_date) = '{filters.get('year')}'"
        
    sql = frappe.db.sql(f"""
            SELECT
                te.name AS `Employee`, 
                te.full_name_ar AS `Employee Name`,
                te.nationality AS `Nationality`,
                CASE
                    WHEN te.nationality <> 'Jordan' THEN te.personal_no
                    ELSE te.national_no
                END AS `National No`,
                te.social_security_number AS `Social Security No`,
                te.personal_no AS `Personal No`,
                '' AS `Facility Number`,
                te.date_of_birth AS `Date Of Birth`,
                te.date_of_joining AS `Date Of Joining`,
                te.social_security_salary AS `Social Security Salary`,
                te.custom_id_card_no AS `ID Card No`,
                tss.total_working_days AS `Working Days`,
                tss.payment_days AS `Payment Days`,
                te.designation AS `Designation`,
                CASE
                    WHEN te.custom_is_hazard = 1 THEN td.hazard_code
                    ELSE ""
                END AS `Hazard Code`
            FROM 
                tabEmployee te
            INNER JOIN
                `tabSalary Slip` tss ON te.name = tss.employee
            INNER JOIN
                `tabDesignation` td ON te.designation = td.name
            WHERE 
                   {conditions} 
                   AND tss.docstatus = 1 
                   AND tss.payment_days >= 16 
                   AND MONTH(tss.posting_date) = '1'
            GROUP BY tss.name
        """, as_dict=True)
    
    return sql

def get_columns(filters):
    if filters and filters.get("damman_template"):
        return [
            {"label": "رقم التأمين", "fieldname": "Social Security No", "fieldtype": "Data", "width": 150},
            {"label": "الاسم", "fieldname": "Employee Name", "fieldtype": "Data", "width": 200},
            {"label": "رقم المنشأة", "fieldname": "Facility Number", "fieldtype": "Data", "width": 150},
            {"label": "الرقم الوطني", "fieldname": "National No", "fieldtype": "Data", "width": 150},
            {"label": "الأجر", "fieldname": "Social Security Salary", "fieldtype": "Currency", "width": 150},
            {"label": "الرقم الشخصي", "fieldname": "Personal No", "fieldtype": "Data", "width": 150},
        ]
        
    return[
        {"label": "Employee", "fieldname": "Employee", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Employee Name", "fieldname": "Employee Name", "fieldtype": "Data", "width": 200},
        {"label": "Nationality", "fieldname": "Nationality", "fieldtype": "Data", "width": 200},
        {"label": "National No/Personal No", "fieldname": "National No", "fieldtype": "Data", "width": 200},
        {"label": "Social Security No", "fieldname": "Social Security No", "fieldtype": "Data", "width": 200},
        {"label": "Date Of Birth", "fieldname": "Date Of Birth", "fieldtype": "Data", "width": 200},
        {"label": "Date Of Joining", "fieldname": "Date Of Joining", "fieldtype": "Data", "width": 200},
        {"label": "Social Security Salary", "fieldname": "Social Security Salary", "fieldtype": "Data", "width": 200},
        {"label": "ID Card No", "fieldname": "ID Card No", "fieldtype": "Data", "width": 200},
        {"label": "Working Days", "fieldname": "Working Days", "fieldtype": "Data", "width": 200},
        {"label": "Payment Days", "fieldname": "Payment Days", "fieldtype": "Data", "width": 200},
        {"label": "Designation", "fieldname": "Designation", "fieldtype": "Data", "width": 200},
        {"label": "Hazard Code", "fieldname": "Hazard Code", "fieldtype": "Data", "width": 200},
    ]
