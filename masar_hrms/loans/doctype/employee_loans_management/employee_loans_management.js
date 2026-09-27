// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Loans Management", {
	employee: function(frm) {
        getBasicSalary(frm);
	},
});


function getBasicSalary(frm) {
    if (frm.doc.employee) {
        frappe.call({
            doc: frm.doc,
            method: "get_basic_salary",
            callback: function(r) {
                if (r.message) {
                    frm.set_value("basic_salary", r.message);
                    frm.refresh_field("basic_salary");
                }
            }
        });
    }
}