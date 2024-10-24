# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
    conditions = " 1=1 "
    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"

    if filters.get('bank'):
        conditions += f" AND te.bank = '{filters.get('bank')}'"
        
    if filters.get('bank_branch'):
        conditions += f" AND te.bank_branch = '{filters.get('bank_branch')}'"
        
    if filters.get('national_no'):
        conditions += f" AND te.national_no LIKE '%{filters.get('national_no')}%'"

    sql = frappe.db.sql(f"""
                        	SELECT 
                         		te.employee, te.employee_name, te.bank, te.bank_branch, tb.swift_number, 
                           		te.iban, te.national_no, tss.gross_pay 
							FROM tabEmployee te 
							LEFT JOIN tabBank tb ON te.bank = tb.name
							LEFT JOIN `tabSalary Slip` tss ON tss.employee = te.employee
							WHERE {conditions}
                         """)
    
    return sql

def get_columns():
    return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Bank: Link/Bank:200",
		"Bank Branch: Link/Bank Branch:200",
		"Swift Code: Data:200",
		"IBAN: Data:200",
		"National No.: Data:200",
		"Net Salary: Currency:200"
	]
