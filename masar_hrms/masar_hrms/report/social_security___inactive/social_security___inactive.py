# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe , calendar

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_data(filters):
    year = int(filters.get("year"))
    month_name = filters.get("month")
    month = list(calendar.month_name).index(month_name)
    current_month = f"{year}-{month:02d}"
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    emp_filter = ''
    if filters.get("employee"): 
        emp_filter = f""" AND e.name = '{filters.get("employee")}' """
    previous_month = f"{prev_year}-{prev_month:02d}"
    data = frappe.db.sql(f"""
        SELECT DISTINCT
            e.national_no,
            e.social_security_number,
            YEAR(e.date_of_birth) AS birth_year,
            MONTH(e.date_of_birth) AS birth_month,
            DAY(e.date_of_birth) AS birth_day,
            ss.employee,
            e.employee_name,
            e.social_security_salary,
            CASE 
                WHEN e.custom_is_hazard = 1 AND td.hazard_code IS NULL THEN 'ERROR CODE'
                WHEN e.custom_is_hazard = 1 THEN td.hazard_code
                ELSE ''
             END AS hazard_code
        FROM `tabSalary Slip` ss
        INNER JOIN `tabSalary Detail` sd 
            ON ss.name = sd.parent
            AND sd.salary_component = 'Social Security'
            AND sd.amount > 0
        INNER JOIN `tabEmployee` e ON ss.employee = e.name
        LEFT JOIN `tabDesignation` td ON td.name = e.designation
        WHERE 
            ss.docstatus = 1 {emp_filter}
            AND DATE_FORMAT(ss.posting_date, '%Y-%m') = '{previous_month}'
            AND ss.employee NOT IN (
                SELECT ss2.employee
                FROM `tabSalary Slip` ss2
                INNER JOIN `tabSalary Detail` sd2
                    ON ss2.name = sd2.parent
                    AND sd2.salary_component = 'Social Security'
                    AND sd2.amount > 0
                WHERE
                    ss2.docstatus = 1
                    AND DATE_FORMAT(ss2.posting_date, '%Y-%m') = '{current_month}'
            )
    """, as_dict=True)
    return data

def get_columns():
    return [
        {"label": "National No", "fieldname": "national_no", "fieldtype": "Data", "width": 150},
        {"label": "Social Security Number", "fieldname": "social_security_number", "fieldtype": "Data", "width": 180},
        {"label": "Birth Year", "fieldname": "birth_year", "fieldtype": "Int", "width": 150},
        {"label": "Birth Month", "fieldname": "birth_month", "fieldtype": "Int", "width": 150},
        {"label": "Birth Day", "fieldname": "birth_day", "fieldtype": "Int", "width": 150},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name" , "fieldname" : "employee_name" , "fieldtype" : "Data" , "width" : 200},
        {"label": "Social Security Salary", "fieldname": "social_security_salary", "fieldtype": "Currency", "width": 150},
        {"label": "Hazard Code", "fieldname": "hazard_code", "fieldtype": "Data", "width": 120},
    ]
