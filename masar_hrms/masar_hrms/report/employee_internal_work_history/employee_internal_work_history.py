# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters=None):
	conditions = "1=1"
	_from, to = filters.get('from'), filters.get('to')
	if filters.get('employee'):
		conditions += f" AND EM.name = '{filters.get('employee')}'"
	if filters.get('department'):
		conditions += f" AND EM.department = '{filters.get('department')}'"
	if filters.get('status'):
		conditions += f" AND EM.status = '{filters.get('status')}'"
	if filters.get('designation'):
		conditions += f" AND EM.designation = '{filters.get('designation')}'"
	if filters.get('work'):
		conditions += f" AND EM.work_type = '{filters.get('work')}'"	
	if _from and to:
		conditions += f" AND EM.date_of_joining BETWEEN '{_from}' AND '{to}'"
    
	sql = frappe.db.sql(f"""
		SELECT 
			EM.name AS `ID`,
			EM.employee_name AS `Employee`,
			EM.full_name_ar AS `Full Name AR`, 
			EM.date_of_joining AS `Date Of Joining`,
			EM.department AS `Current Department`,
			EM.designation AS `Current Designation`,
			EM.work_type AS `Work Type`,
			EM.status AS `Status`,				 
			EEWH.department AS `Internal WH Department`, 
			EEWH.designation AS `Internal WH Designation`, 
			EEWH.from_date AS `Internal WH From Date`, 
			EEWH.to_date AS `Internal WH To Date`,
			CONCAT(
				TIMESTAMPDIFF(YEAR, EM.date_of_joining, CURDATE()), ' years, ',
				TIMESTAMPDIFF(MONTH, EM.date_of_joining, CURDATE()) % 12, ' months'
			) AS `Years in Company`
		FROM `tabEmployee` AS EM
		LEFT JOIN `tabEmployee Internal Work History` EEWH ON EEWH.parent = EM.name AND EM.designation != EEWH.designation
		WHERE {conditions} 
	""", as_list=True)

	return sql

def get_columns():
	return [
		"ID:Link/Employee:150",
		"Employee:Data:200",
		"Full Name AR:Data:200",
		"Date Of Joining:Date:130",
		"Current Department:Link/Department:180",
		"Current Designation:Link/Designation:180",
		"Work Type:Data:120",
		"Status:Data:100",
		"Internal WH Department:Data:180",
		"Internal WH Designation:Data:180",
		"Internal WH From Date:Date:150",
		"Internal WH To Date:Date:150",
		"Years in Company:Data:150",
	]
