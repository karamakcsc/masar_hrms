// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Repost Component Variance"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "view",
			label: __("View"),
			fieldtype: "Select",
			options: ["Component Summary", "Employee Detail"],
			default: "Component Summary",
		},
		{
			fieldname: "status",
			label: __("Repost Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Pending", "Applied"],
		},
		{
			fieldname: "component_type",
			label: __("Component Type"),
			fieldtype: "Select",
			options: ["", "Earning", "Deduction"],
		},
		{
			fieldname: "payroll_entry",
			label: __("Payroll Entry"),
			fieldtype: "Link",
			options: "Payroll Entry",
		},
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
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) value = `<b>${value}</b>`;
		if (data && column.fieldname === "difference" && data.difference) {
			const color = data.difference > 0 ? "var(--green-600)" : "var(--red-500)";
			value = `<span style="color: ${color}">${value}</span>`;
		}
		return value;
	},
};
