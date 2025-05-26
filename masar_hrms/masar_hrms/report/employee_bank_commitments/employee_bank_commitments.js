// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Bank Commitments"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "bank",
			label: __("Bank"),
			fieldtype: "Link",
			options: "Bank",
		},
	]
};
