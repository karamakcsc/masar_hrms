// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Payroll Budget Cumulative Expense"] = {
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
			fieldname: "budget_element",
			label: __("Budget Element"),
			fieldtype: "Link",
			options: "Budget Element",
			get_query: () => {
				const project = frappe.query_report.get_filter_value("project");
				return { filters: project ? { project, docstatus: 1 } : { docstatus: 1 } };
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_end(),
			reqd: 1,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && !data.month) value = `<b>${value}</b>`;
		if (data && column.fieldname === "remaining_budget" && data.remaining_budget < 0) {
			value = `<span style="color: var(--red-500)">${value}</span>`;
		}
		return value;
	},
};
