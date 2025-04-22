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
				te.grade,
				MAX(CASE
					WHEN test.salary_component = 'Basic' AND test.is_active = 1 
					THEN test.esc_amount
				END) AS `Basic Salary`,
				te.social_security_salary,
				te.date_of_joining,
				CONCAT(
					TIMESTAMPDIFF(YEAR, te.date_of_joining, CURDATE()), ' years and ',
					TIMESTAMPDIFF(MONTH, te.date_of_joining, CURDATE()) % 12, ' months'
				) AS `Internal Total Experience`,
				CONCAT(
					FLOOR(SUM(IFNULL(teewh.total_experience, 0)) / 12), ' years and ',
					MOD(SUM(IFNULL(teewh.total_experience, 0)), 12), ' months'
				) AS `External Total Experience`,
				te.custom_latest_education,
				te.custom_major,
				te.custom_is_engineer
			FROM tabEmployee te 
			INNER JOIN `tabEmployee Salary Table` test ON test.parent = te.name
			LEFT JOIN `tabEmployee External Work History` teewh ON teewh.parent = te.name
			WHERE {conditions}
			GROUP BY te.name
			ORDER BY te.name ASC
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
		"Grade: Data:200",
		"Basic Salary: Currency:200",
		"Social Security Salary: Currency:200",
		"Date Of Joining: Date:200",
		"Internal Total Experience: Data:200",
		"External Total Experience: Data:200",
		"Latest Education: Data:200",
		"Major: Data:200",
		"Is Engineer: Check:100"
	]
	return columns
