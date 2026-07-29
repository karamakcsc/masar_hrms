frappe.query_reports["Payroll Impact Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname": "work_injury",
			"label": __("Work Injury"),
			"fieldtype": "Link",
			"options": "Work Injury",
		},
	],
};
