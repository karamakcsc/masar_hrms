// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Salary Details"] = {
	"filters": [
		{
			"fieldname": "ss_no",
			"label": __("Salary Slip"),
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "from",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default": dateutil.year_start()
		 },
		 {
			"fieldname": "to",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default": dateutil.year_end()
		},
	  {
			"fieldname": "emp_name",
			"label": __("Employee Name"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "dep",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
			"reqd": 0,
		},
		{
			"fieldname": "des",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
			"width": 150,
			"reqd": 0,
		}
		// {
		// 	"fieldname": "tax_category",
		// 	"label": __("Tax Group"),
		// 	"fieldtype": "Link",
		// 	"options": "Tax Category",
		// 	"width": 100,
		// 	"reqd": 0,
		// },
		// {
		// 					"fieldname": "is_return",
		// 					"label": __("Is Return"),
		// 					"fieldtype": "Check",
		// 					//"options": "Is Return",
		// 					"width": 100,
		// 					"reqd": 0,
		// 				}

]
};
