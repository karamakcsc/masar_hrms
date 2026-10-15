// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

const RSS_METHOD = "masar_hrms.repost_payroll_and_slips.doctype.repost_salary_slip.repost_salary_slip";
const RSS_RECALCULATE_FIELDS = [
	"department",
	"designation",
	"branch",
	"grade",
	"section",
	"work_type",
	"is_social_security_applicable",
	"social_security_salary",
	"is_hazard",
];

frappe.ui.form.on("Repost Salary Slip", {
	setup(frm) {
		frm.set_query("salary_slip", () => ({
			filters: { docstatus: 1, journal_entry: ["is", "set"], payroll_entry: ["is", "set"] },
		}));
		frm.set_query("salary_component", "earnings", () => ({ filters: { type: "Earning", disabled: 0 } }));
		frm.set_query("salary_component", "deductions", () => ({ filters: { type: "Deduction", disabled: 0 } }));
	},

	onload(frm) {
		frappe.call({
			method: `${RSS_METHOD}.get_dimension_options`,
			callback(r) {
				Object.entries(r.message || {}).forEach(([field, options]) => {
					frm.set_df_property(field, "options", options);
				});
				frm.refresh_fields(["section", "work_type"]);
			},
		});
	},

	refresh(frm) {
		frm.trigger("apply_project_dimensions");
		frm.trigger("set_indicator");
		if (frm.doc.salary_slip) {
			frm.add_custom_button(__("Salary Slip"), () => frappe.set_route("Form", "Salary Slip", frm.doc.salary_slip), __("View"));
		}
		if (frm.doc.repost_payroll) {
			frm.add_custom_button(__("Repost Payroll"), () => frappe.set_route("Form", "Repost Payroll", frm.doc.repost_payroll), __("View"));
		}
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending" && frm.doc.payroll_entry) {
			frm.add_custom_button(__("Repost Payroll"), () => {
				frappe.new_doc("Repost Payroll", { payroll_entry: frm.doc.payroll_entry });
			}, __("Create"));
		}
	},

	set_indicator(frm) {
		const colors = { Draft: "red", Pending: "orange", Applied: "green", Cancelled: "grey" };
		if (frm.doc.status && !frm.is_new()) {
			frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "blue");
		}
	},

	salary_slip(frm) {
		if (!frm.doc.salary_slip) return;
		frm.call({ doc: frm.doc, method: "load_salary_slip", freeze: true }).then(() => {
			frm.trigger("apply_project_dimensions");
		});
	},

	project(frm) {
		frm.trigger("apply_project_dimensions");
		frm.events.recalculate(frm);
	},

	apply_project_dimensions(frm) {
		frappe.call({
			method: `${RSS_METHOD}.get_enabled_dimensions`,
			args: { project: frm.doc.project || null },
			callback(r) {
				const config = r.message || {};
				const editable = frm.doc.docstatus === 0 && !!frm.doc.salary_slip;
				(config.all_dimensions || []).forEach((field) => {
					const enabled = !config.budget_enabled || (config.dimensions || []).includes(field);
					frm.set_df_property(field, "read_only", editable && enabled ? 0 : 1);
					frm.set_df_property(field, "reqd", config.budget_enabled && enabled ? 1 : 0);
				});
				frm.set_df_property("project", "read_only", editable ? 0 : 1);

				if (config.budget_enabled && frm.doc.project && !config.configured) {
					frm.dashboard.set_headline(
						__("Project {0} is not configured in Payroll Budget Settings.", [frm.doc.project.bold()]),
						"red"
					);
				} else {
					frm.dashboard.clear_headline();
				}
			},
		});
	},

	recalculate: frappe.utils.debounce((frm) => {
		if (!frm.doc.salary_slip || frm.doc.docstatus !== 0) return;
		frm.call({ doc: frm.doc, method: "recalculate" });
	}, 400),
});

RSS_RECALCULATE_FIELDS.forEach((field) => {
	frappe.ui.form.on("Repost Salary Slip", field, (frm) => frm.events.recalculate(frm));
});

frappe.ui.form.on("Repost Salary Slip", {
	earnings_remove: (frm) => frm.events.recalculate(frm),
	deductions_remove: (frm) => frm.events.recalculate(frm),
	before_deductions_remove(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.is_social_security) {
			frappe.throw(__("The Social Security deduction is calculated. Change the Social Security section instead."));
		}
		if (row.is_income_tax) {
			frappe.throw(__("Income Tax is calculated from the earnings and cannot be removed."));
		}
	},
});

frappe.ui.form.on("Repost Salary Detail", {
	salary_component: (frm) => frm.events.recalculate(frm),
	amount(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.is_social_security || row.is_income_tax) {
			frappe.show_alert({
				message: row.is_income_tax
					? __("Income Tax is calculated from the earnings; your value will be replaced.")
					: __("The Social Security deduction is calculated from the Social Security section."),
				indicator: "orange",
			});
		}
		frm.events.recalculate(frm);
	},
});
