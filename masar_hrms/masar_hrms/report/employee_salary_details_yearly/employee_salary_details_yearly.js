// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Salary Details Yearly"] = {
	"filters": [
		{
			"fieldname": "from",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default":  frappe.datetime.year_start()
		 },
		 {
			"fieldname": "to",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default":  frappe.datetime.year_end()
		},
	  	{
			"fieldname": "emp_name",
			"label": __("Employee Name"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
			"reqd": 0,
		},
	]
};
