// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Repost Payroll", {
	setup(frm) {
		frm.set_query("payroll_entry", () => ({ filters: { docstatus: 1 } }));
	},

	refresh(frm) {
		const colors = { Draft: "red", Completed: "green", Cancelled: "grey" };
		if (frm.doc.status && !frm.is_new()) {
			frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "blue");
		}
		if (frm.doc.payroll_entry) {
			frm.add_custom_button(__("Payroll Entry"), () => frappe.set_route("Form", "Payroll Entry", frm.doc.payroll_entry), __("View"));
		}
		if (frm.doc.new_journal_entry) {
			frm.add_custom_button(__("New Journal Entry"), () => frappe.set_route("Form", "Journal Entry", frm.doc.new_journal_entry), __("View"));
		}
		if (frm.doc.docstatus === 0 && frm.doc.payroll_entry) {
			frm.add_custom_button(__("Prepare Salary Slip Repost"), () => {
				frappe.new_doc("Repost Salary Slip");
			});
		}
	},

	payroll_entry(frm) {
		frm.trigger("get_reposts");
	},

	get_reposts(frm) {
		if (!frm.doc.payroll_entry) {
			frm.clear_table("reposts");
			frm.refresh_field("reposts");
			return;
		}
		frm.call({ doc: frm.doc, method: "get_reposts", freeze: true }).then(() => {
			if (!(frm.doc.reposts || []).length) {
				frappe.show_alert({
					message: __("No pending Repost Salary Slip for Payroll Entry {0}.", [frm.doc.payroll_entry]),
					indicator: "orange",
				});
			}
		});
	},
});
