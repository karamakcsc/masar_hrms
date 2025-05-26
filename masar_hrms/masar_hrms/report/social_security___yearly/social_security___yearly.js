// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Social Security - Yearly"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Data",
			"width": 80,
			// "default":  frappe.datetime.year_start()
		 },
		// {
		// 	"fieldname": "month",
		// 	"label": __("Months"),
		// 	"fieldtype": "Data",
		// 	"width": 80,
		// 	// "default":  frappe.datetime.year_start()
		//  },
		// {
		// 	"fieldname": "from",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"width": 80,
		// 	"default":  frappe.datetime.month_start()
		//  },
		//  {
		// 	"fieldname": "to",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	"width": 80,
		// 	"default":  frappe.datetime.month_end()
		// },
	]
};
