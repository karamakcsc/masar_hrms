// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Loan Management History Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "management_type",
			"label": __("Management Type"),
			"fieldtype": "Select",
			"options": "\nReschedule\nRestructure",
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nSubmitted\nCancelled",
		},
	]
};
