// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Payroll Budget Mapping"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "status",
			label: __("Employee Status"),
			fieldtype: "Select",
			options: ["Active", "Inactive", "Suspended", "Left"],
			default: "Active",
		},
		{
			fieldname: "only_not_mapped",
			label: __("Only Not Mapped"),
			fieldtype: "Check",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && column.fieldname === "mapping_status") {
			const color = data.mapping_status === "Mapped" ? "green" : "red";
			value = `<span class="indicator-pill ${color}">${value}</span>`;
		}
		return value;
	},
};
