// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on('Employee Shift Management', {
    before_save: function (frm) {
        frappe.call({
            method: "masar_hrms.masar_hrms.doctype.employee_shift_management.employee_shift_management.check_active_status",
            args: {
                employee :frm.doc.employee ,  
            },
            callback: function (r) {
                if (r.message === 1) {
                    frappe.validated = false;
                    frappe.throw(__("Employee: "+frm.doc.employee +" Alredy Exist With Active Status."));
                }
            }
        });
    },
    on_submit: function (frm) {
        frappe.call({
            method: "masar_hrms.masar_hrms.doctype.employee_shift_management.employee_shift_management.create_shift_assignment",
            args: {
                name: frm.doc.name
            },
            callback: function (r) {
                frappe.msgprint(r.message);
            }
        });
    },
});

