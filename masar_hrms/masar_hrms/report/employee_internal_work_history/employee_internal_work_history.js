// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Internal Work History"] = {
	"filters": [
		
			{
				"fieldname": "employee",
				"label": "Employee",
				"fieldtype": "Link",
				"options": "Employee"
			},
			{
				"fieldname": "department",
				"label": "Department",
				"fieldtype": "Link",
				"options": "Department"
			},
			{
				"fieldname": "designation",
				"label": "Designation",
				"fieldtype": "Link",
				"options": "Designation"
			},
			{
				"fieldname": "status",
				"label": "Status",
				"fieldtype": "Select",
				"options": "\nActive\nLeft\nSuspended",
				"default": "Active"
			},
			{
				"fieldname": "from",
				"label": "From Date",
				"fieldtype": "Date"
			},
			{
				"fieldname": "to",
				"label": "To Date",
				"fieldtype": "Date"
			},
			{
				"fieldname":"work",
				"label" : "Work Type",
				"fieldtype" : "Select",
				"options":"\nDaily\nMonthly"
			}
		]

};
