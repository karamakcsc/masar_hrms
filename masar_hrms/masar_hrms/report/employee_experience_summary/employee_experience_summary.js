// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Experience Summary"] = {
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
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "from",
			"label": __("From Joining Date"),
			"fieldtype": "Date",
			"width": 100,
		 },
		 {
			"fieldname": "to",
			"label": __("To Joining Date"),
			"fieldtype": "Date",
			"width": 100,
		},

	]
};
