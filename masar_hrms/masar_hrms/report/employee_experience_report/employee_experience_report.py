# Copyright (c) 2024, KCSC and contributors
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
       						te.department AS `Department`,
							te.date_of_joining AS `Date Of Joining`,
       						teiwh.department AS `Internal WH Department`, 
             				teiwh.designation AS `Internal WH Designation`, 
                 			teiwh.from_date AS `Internal WH From Date`, 
                    		teiwh.to_date AS `Internal WH To Date`,
							teewh.company_name AS `External WH Company`, 
       						teewh.designation AS `External WH Designation`, 
             				teewh.salary AS `External WH Salary`, 
                 			teewh.custom_from_date AS `External WH From Date`, 
                    		teewh.custom_to_date AS `External WH To Date`, 
       						teewh.total_experience AS `External WH Total Experience MM`
						FROM 
      						tabEmployee te
						LEFT JOIN 
      						`tabEmployee Internal Work History` teiwh ON teiwh.parent = te.name 
						LEFT JOIN 
      						`tabEmployee External Work History` teewh ON teewh.parent = te.name 
						WHERE 
      						{conditions} AND te.status = 'Active'
						GROUP BY
							teiwh.name, teewh.name
						ORDER BY 
      						te.name ASC;
					""")
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Department: Link/Department:200",
		"Date Of Joining: Date:200",
		"Internal WH Department: Data:200",
		"Internal WH Designation: Data:200",
		"Internal WH From Date: Date:200",
		"Internal WH To Date: Date:200",
		"External WH Company: Data:200",
		"External WH Designation: Data:200",
		"External WH Salary: Float:200",
		"External WH From Date: Date:200",
		"External WH To Date: Date:200",
		"External WH Total Experience MM: Float:200",
	]