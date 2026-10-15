// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Repost Salary Slip Register"] = {
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
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Pending", "Applied", "Cancelled"],
		},
		{
			fieldname: "payroll_entry",
			label: __("Payroll Entry"),
			fieldtype: "Link",
			options: "Payroll Entry",
		},
		{
			fieldname: "repost_payroll",
			label: __("Repost Payroll"),
			fieldtype: "Link",
			options: "Repost Payroll",
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
		{
			fieldname: "include_cancelled",
			label: __("Include Cancelled"),
			fieldtype: "Check",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "status") {
			const color = { Draft: "red", Pending: "orange", Applied: "green", Cancelled: "gray" }[
				data.status
			];
			if (color) value = `<span class="indicator-pill ${color}">${value}</span>`;
		}
		if (column.fieldname.endsWith("_difference") && data[column.fieldname]) {
			const color = data[column.fieldname] > 0 ? "var(--green-600)" : "var(--red-500)";
			value = `<span style="color: ${color}">${value}</span>`;
		}
		return value;
	},
};
