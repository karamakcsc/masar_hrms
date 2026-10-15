// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Payroll Budget vs Actual"] = {
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
			fieldname: "budget_type",
			label: __("Budget Type"),
			fieldtype: "Select",
			options: ["", "Salary", "Social Security"],
		},
		{
			fieldname: "fiscal_year",
			label: __("Budget Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["Budget Element", "Project"],
			default: "Budget Element",
		},
		{
			fieldname: "only_exceeded",
			label: __("Only Exceeded"),
			fieldtype: "Check",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (data.bold) value = `<b>${value}</b>`;

		if (column.fieldname === "status") {
			const color = {
				Exceeded: "red",
				"Near Limit": "orange",
				"Within Budget": "green",
				"Not Used": "gray",
			}[data.status];
			if (color) value = `<span class="indicator-pill ${color}">${value}</span>`;
		}
		if (column.fieldname === "remaining_budget" && data.remaining_budget < 0) {
			value = `<span style="color: var(--red-500)">${value}</span>`;
		}
		return value;
	},
};
