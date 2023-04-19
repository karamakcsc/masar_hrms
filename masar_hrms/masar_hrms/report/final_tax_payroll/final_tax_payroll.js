// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Final TAX Payroll"] = {
	"filters": [
		{
			"fieldname": "ss_no",
			"label": __("Social Security Number"),
			"fieldtype": "Data",
			// "options": "Salary Slip",
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
		},
		{
			"fieldname": "work_type",
			"label": __("Work Type"),
			"fieldtype": "Select",
			"options": ["\n","Daily","Monthly"],
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 100,
			"reqd": 0,
		}

]
};
