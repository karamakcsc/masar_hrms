# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    _from, to = filters.get('from'), filters.get('to')
    if filters.get('employee'):
        conditions += f" AND te.name = '{filters.get('employee')}'"
    if filters.get('department'):
        conditions += f" AND te.department = '{filters.get('department')}'"
    if filters.get('designation'):
        conditions += f" AND te.designation = '{filters.get('designation')}'"
    if _from and to:
        conditions += f" AND te.date_of_joining BETWEEN '{_from}' AND '{to}'"
        
    sql = frappe.db.sql(f"""
                        SELECT DISTINCT
							te.name AS `Employee`, 
       						te.employee_name AS `Employee Name`,
       						te.department AS `Current Department`,
							te.designation AS `Current Designation`,
							te.date_of_joining AS `Date Of Joining`, 
							TIMESTAMPDIFF(MONTH, te.date_of_joining, CURDATE()) AS `Internal Total Experience (Months)`,
       						SUM(IFNULL(teewh.total_experience, 0)) AS `External Total Experience (Months)`
						FROM 
      						tabEmployee te
						LEFT JOIN 
      						`tabEmployee Internal Work History` teiwh ON teiwh.parent = te.name 
						LEFT JOIN 
      						`tabEmployee External Work History` teewh ON teewh.parent = te.name 
						WHERE 
      						{conditions} AND te.status = 'Active'
						GROUP BY
							te.name
						ORDER BY 
      						te.name ASC;
					""")
    
    return sql


def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Current Department: Link/Department:200",
		"Current Designation: Data:200",
		"Date Of Joining: Date:150",
		"Internal Total Experience (Months): Data:250",
		"External Total Experience (Months): Data:250"
	]