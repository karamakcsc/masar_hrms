// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

const PAYROLL_DIMENSIONS = ["Department", "Designation", "Branch", "Grade", "Section", "Work Type"];

frappe.ui.form.on("Payroll Project Dimension Settings", {
	select_dimensions(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const selected = (row.dimensions || "")
			.split(",")
			.map((d) => d.trim())
			.filter(Boolean);

		const dialog = new frappe.ui.Dialog({
			title: __("Dimensions for {0}", [row.project || __("Project")]),
			fields: [
				{
					fieldname: "dimensions",
					fieldtype: "MultiCheck",
					columns: 2,
					options: PAYROLL_DIMENSIONS.map((d) => ({
						label: __(d),
						value: d,
						checked: selected.includes(d),
					})),
				},
			],
			primary_action_label: __("Set"),
			primary_action(values) {
				// keep canonical order
				const picked = PAYROLL_DIMENSIONS.filter((d) => (values.dimensions || []).includes(d));
				frappe.model.set_value(cdt, cdn, "dimensions", picked.join(", "));
				dialog.hide();
			},
		});
		dialog.show();
	},

	enable_multi_dimension(frm, cdt, cdn) {
		if (!locals[cdt][cdn].enable_multi_dimension) {
			frappe.model.set_value(cdt, cdn, "dimensions", "");
		}
	},
});
