frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !frm.doc.payroll_entry || !frm.doc.journal_entry) return;
		if (!frappe.model.can_create("Repost Salary Slip")) return;
		frm.add_custom_button(__("Repost Salary Slip"), () => {
			frappe.new_doc("Repost Salary Slip", { salary_slip: frm.doc.name });
		}, __("Create"));
	},
});
