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
			"label": __("University/College"),
			"fieldtype": "Link",
			"options": "Institution",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname": "major",
			"label": __("Major"),
			"fieldtype": "Link",
			"options": "Major",
			"width": 100,
			"reqd": 0,
		},
		{
			"fieldname" : "level", 
			"label" : "Level/Degree",
			"fieldtype": "Select",
			"options": "\nHigh School\nDiploma\nBachelor's\nMaster's\nPh.D.",
			"width": 100,
			"reqd": 0
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
