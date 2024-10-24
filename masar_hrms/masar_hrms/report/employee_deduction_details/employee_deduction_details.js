// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Deduction Details"] = {
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
			"fieldname": "salary_component",
			"label": __("Salary Component"),
			"fieldtype": "Link",
			"options": "Salary Component",
			"width": 100,
			"reqd": 0,
			"get_query": function () {
				return {
					"filters": {
						"type": "Deduction"
					}
				};
			}
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 100,
			"reqd": 0,
		},
	]
};
