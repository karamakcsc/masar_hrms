// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Cumulative Salary And Tax"] = {
	"filters": [
		{
			"fieldname": "from",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": 80,
		 },
		 {
			"fieldname": "to",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": 80,
		},
	  	{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 100,
		},
	]
};
