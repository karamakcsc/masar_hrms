// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Payroll Budget", {
	setup(frm) {
		["employee_salary_budget", "company_social_security_budget"].forEach((field) => {
			frm.set_query(field, "budget_dimensions", () => ({
				filters: frm.doc.project ? { project: frm.doc.project, docstatus: 1 } : { docstatus: 1 },
			}));
		});
	},

	refresh(frm) {
		frm.trigger("apply_project_dimensions");
	},

	project(frm) {
		frm.trigger("apply_project_dimensions");
	},

	apply_project_dimensions(frm) {
		frappe.call({
			method: "masar_hrms.payroll_budget.utils.get_project_dimension_config",
			args: { project: frm.doc.project || null },
			callback(r) {
				const config = r.message || {};
				const enabled = config.dimensions || [];
				const grid = frm.fields_dict.budget_dimensions.grid;

				Object.entries(config.budget_fields || {}).forEach(([label, fieldname]) => {
					const is_enabled = enabled.includes(label);
					grid.update_docfield_property(fieldname, "hidden", is_enabled ? 0 : 1);
					grid.update_docfield_property(fieldname, "reqd", is_enabled ? 1 : 0);
				});
				grid.reset_grid();

				if (frm.doc.project && !config.configured) {
					frm.dashboard.set_headline(
						__("Project {0} is not configured in Payroll Budget Settings.", [
							frm.doc.project.bold(),
						]),
						"red"
					);
				} else {
					frm.dashboard.clear_headline();
				}
			},
		});
	},
});
