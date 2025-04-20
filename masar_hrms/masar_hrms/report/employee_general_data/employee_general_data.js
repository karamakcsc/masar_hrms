// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee General Data"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive\nLeft\nSuspended",
			"default": "Active",
		}
	]
};
