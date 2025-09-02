# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_data(filters):
	conditions = " 1=1 "
	if filters.get('employee'):
		conditions += f" AND te.employee = '{filters.get('employee')}'"
	if filters.get('provider'):
		conditions += f" AND tee.custom_training_provider = '{filters.get('provider')}'"
	if filters.get('is_engineer'):
		conditions += f" AND te.custom_is_engineer = '{filters.get('is_engineer')}'"

	sql = frappe.db.sql(f"""
						SELECT 
							te.name AS `Employee`, 
							te.employee_name AS `Employee Name`, 
							tee.custom_training_provider AS `Training Provider`, 
							tee.custom_training_provider_ar AS `Training Provider (AR)`,
							tee.custom_certificate_name AS `Certificate Name`, 
							tee.custom_issue_date AS `Issue Date`, 
							tee.custom_total_hours AS `Total Hours`,
							CASE
       							WHEN tee.custom_is_certificate = 1 Then 'Yes'
								ELSE 'No'
       						END AS `Is Certificate`,
							CASE 
								WHEN te.custom_is_engineer = 1 Then 'Yes'
								ELSE 'No'
							END AS `Is Engineer`,
							tee.custom_remarks AS `Remarks`
						FROM tabEmployee te
						LEFT JOIN 
							`tabEmployee Education` tee ON tee.parent = te.name
						WHERE {conditions} AND tee.custom_is_training = 1
						ORDER BY
							te.name ASC;
					""")

	return sql

def get_columns():
	return [
		"Employee: Link/Employee:200",
		"Employee Name: Data:200",
		"Training Provider: Link:200",
		"Training Provider (AR): Data:200",
		"Certificate Name: Data:200",
		"Issue Date: Data:200",
		"Total Hours: Int:200",
		"Is Certificate: Data:200",
		"Is Engineer: Data:100",
		"Remarks: Data:300",
	]