// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Bank Details"] = {
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
			"fieldname": "bank",
			"label": __("Bank"),
			"fieldtype": "Link",
			"options": "Bank",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "bank_branch",
			"label": __("Bank Branch"),
			"fieldtype": "Link",
			"options": "Bank Branch",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "national_no",
			"label": __("National No."),
			"fieldtype": "Data",
			"width": 100,
			"reqd": 0,
		},
	]
};
