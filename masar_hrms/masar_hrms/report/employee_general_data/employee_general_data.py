# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND te.name = '{filters.get('employee')}' "
    if filters.get('department'):
        conditions += f" AND te.department = '{filters.get('department')}' "
    if filters.get('status'):
        conditions += f" AND te.status = '{filters.get('status')}' "
    sql = frappe.db.sql(f"""
            SELECT 
				te.name, 
				te.employee_name, 
				te.full_name_ar, 
				te.department, 
				te.designation, 
				te.status, 
				te.custom_years_at_the_company, 
				te.grade,
				te.basic_salary,
				te.social_security_salary,
				te.custom_latest_education,
				te.custom_major,
				te.custom_is_engineer
			FROM tabEmployee te 
			WHERE {conditions}
        """)
    
    return sql


def get_columns():
	columns = [
		"Employee No.:Link/Employee:200",
		"Employee Name: Data:200",
		"Full Name Arabic: Data:200",
		"Department: Data:200",
		"Designation: Data:200",
		"Status: Data:200",
		"Years At The Company: Data:200",
		"Grade: Data:200",
		"Basic Salary: Currency:200",
		"Social Security Salary: Currency:200",
		"Latest Education: Data:200",
		"Major: Data:200",
		"Is Engineer: Check:100"
	]
	return columns
