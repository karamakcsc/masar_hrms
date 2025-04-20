// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Salary Details Total"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 100,
			"reqd": 1,
			"default": frappe.defaults.get_default("company"),
		},
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
			"fieldname": "work_type",
			"label": __("Work Type"),
			"fieldtype": "Select",
			"options": ["\n","Daily","Monthly"],
			"width": 100,
			"reqd": 0,
		},
	]
};
