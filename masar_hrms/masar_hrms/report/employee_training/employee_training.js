// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Training"] = {
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
			"fieldname": "provider",
			"label": __("Training Provider"),
			"fieldtype": "Link",
			"options": "Training Provider",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "is_engineer",
			"label": __("Is Engineer"),
			"fieldtype": "Check",
			"width": 100,
			"reqd": 0,
		},
	]
};
