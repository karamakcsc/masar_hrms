frappe.ui.form.on("Payroll Entry", {
	custom_cuttoff_date: function (frm) {
		frm.trigger("payroll_frequency");
	},
	payroll_frequency: function (frm) {
		if (!frm.doc.payroll_frequency) return;
		frappe.call({
			method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates",
			args: {
				payroll_frequency: frm.doc.payroll_frequency,
				start_date: frm.doc.posting_date,
				company: frm.doc.company,
				custom_cuttoff_date: frm.doc.custom_cuttoff_date,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("start_date", r.message.start_date);
					frm.set_value("end_date", r.message.end_date);
				}
			},
		});
	},
});
