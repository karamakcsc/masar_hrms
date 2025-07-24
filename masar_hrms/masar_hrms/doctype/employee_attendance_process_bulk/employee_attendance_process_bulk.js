// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Attendance Process Bulk", {
	refresh:function(frm) {
        InsertEmployeeButton(frm);
         GetStandardDatePeriod(frm);
	},
    setup: function(frm) {
        InsertEmployeeButton(frm);
         GetStandardDatePeriod(frm);
	},
    onload:function(frm) {
        InsertEmployeeButton(frm);
         GetStandardDatePeriod(frm);
	},
    posting_date: function(frm) {
        GetStandardDatePeriod(frm);
    },
});

function InsertEmployeeButton(frm) {
    if ( frm.doc.docstatus === 0){
    frm.add_custom_button(__("Employees"), function () {
            frappe.call({
                doc: frm.doc,
                method: 'insert_employees',
                callback: function (r) {
                    frm.refresh_field('employees');
                }
            });
        }, __("Insert"));
    }
}
function GetStandardDatePeriod(frm) {
    if (!frm.doc.from_date && !frm.doc.to_date) {
        frappe.call({
            doc: frm.doc,
            method: 'get_standard_date_period',
            callback: function(r) {
                if (r.message){
                frm.doc.from_date = r.message.from_date;
                frm.doc.to_date = r.message.to_date;
                frm.refresh_field('from_date');
                frm.refresh_field('to_date');
            }
        }
        });
    }
}