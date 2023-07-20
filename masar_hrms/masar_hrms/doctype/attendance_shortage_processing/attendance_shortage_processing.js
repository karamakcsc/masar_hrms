// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Shortage Processing', {
	// refresh: function(frm) {

	// }
});



frappe.ui.form.on('Attendance Shortage Processing', {
    setup: function(frm) {
            frappe.call({
                method: "masar_hrms.masar_hrms.doctype.attendance_shortage_processing.attendance_shortage_processing.get_salary_structure_assignment",
                args: {
                    employee: frm.doc.employee
                },
                callback: function(r) {
                    if (r && r.message) {
                        frm.set_value('salary_structure_assignment', r.message);
                    } else {
                        frappe.msgprint("This Employee Don't Have Salary Structure Assignment.");
                    }
                }
            });
    }
});


cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"type": "Deduction"
		}
	}
}
