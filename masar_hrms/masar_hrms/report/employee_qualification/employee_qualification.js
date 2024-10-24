// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Qualification"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "school",
			"label": __("School/Uni"),
			"fieldtype": "Data",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "qualification",
			"label": __("Qualification"),
			"fieldtype": "Data",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "major",
			"label": __("Major"),
			"fieldtype": "Data",
			"width": 100,
			"reqd": 0,
		}
	]
};
