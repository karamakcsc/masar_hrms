// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("AR 3 Print", {
	get_salary_slips: function(frm) {
        addChild(frm);
	},
});

function addChild(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        frappe.call({
            doc: frm.doc,
            method: "get_ss",
            callback: function(r) {
                console.log("Success");
                if (r.message) {
                    frm.clear_table('ss_table');
                    r.message.forEach(emp => {
                        var row = frm.add_child("ss_table");
                        row.salary_slip = emp.name;
                        row.employee = emp.employee;
                        row.employee_name = emp.employee_name;
                        
                    });
                    frm.refresh_field('ss_table');
                }
            }
        })
    }
}