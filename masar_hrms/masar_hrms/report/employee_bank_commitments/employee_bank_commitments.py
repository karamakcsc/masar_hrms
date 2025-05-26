# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    if filters.get("employee"):
        conditions += f" AND te.name = '{filters.get('employee')}'"
    if filters.get("department"):
        conditions += f" AND te.department = '{filters.get('department')}'"
    if filters.get("bank"):
        conditions += f" AND te.bank = '{filters.get('bank')}'"
    
        
    sql = frappe.db.sql(f"""
        SELECT 
        	te.name, 
         	te.employee_name,
			te.department,
   			te.designation,
           	te.bank,
            tb.swift_number, 
            te.bank_ac_no,
            te.iban 
		FROM tabEmployee te
		LEFT JOIN tabBank tb ON te.bank = tb.name 
		WHERE {conditions} AND te.status = 'Active' AND te.custom_is_bank_commitments = 1
	""")
    
    return sql

def get_columns():
    columns = [
		"Employee ID:Link/Employee:150",
		"Employee Name::150",
		"Department::150",
		"Designation::200",
		"Bank:Link/Bank:150",
		"Swift Number::150",
  		"Bank Account No::200",
		"IBAN::150",
	]
    
    return columns
