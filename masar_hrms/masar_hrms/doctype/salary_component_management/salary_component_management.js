// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Component Management", {

    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            // Button: show all log entries created by this specific SCM submission
            frm.add_custom_button(__('Salary Log'), function() {
                frappe.set_route('List', 'Employee Salary Log', {
                    voucher_type: 'Salary Component Management',
                    voucher_no:   frm.doc.name
                });
            }, __('View'));

            // Button: show full salary history for this employee
            frm.add_custom_button(__('Employee Salary History'), function() {
                frappe.set_route('List', 'Employee Salary Log', {
                    employee: frm.doc.employee
                });
            }, __('View'));
        }
    },

    employee: function(frm) {
        frappe.call({
            doc:      frm.doc,
            method:   'get_exist_setting_from_employee',
            args:     { employee: frm.doc.employee },
            callback: function(r) { frm.refresh_fields(); }
        });
    },

    social_security_salary: function(frm) {
        frappe.call({
            doc:      frm.doc,
            method:   'calculate_salry_details_section',
            callback: function(r) { frm.refresh_fields(); }
        });
    },

    edit_ss_salary: function(frm) {
        frappe.call({
            doc:      frm.doc,
            method:   'calculate_salry_details_section',
            callback: function(r) { frm.refresh_fields(); }
        });
    },
});
