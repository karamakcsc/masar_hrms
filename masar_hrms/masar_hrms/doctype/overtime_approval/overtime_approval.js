frappe.ui.form.on('Overtime Approval', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.set_intro(
				__('This approval is submitted. The approved hours will be used as defaults in the Employee Attendance Process.'),
				'green'
			);
		}
	}
});

frappe.ui.form.on('Overtime Approval Detail', {
	approved_hours: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (flt(row.approved_hours) <= 0) {
			frappe.model.set_value(cdt, cdn, 'approved_hours', 0);
			frappe.msgprint(__('Approved Overtime Hours must be greater than zero.'));
		}
	}
});
