// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Attendance Management Bulk", {
	refresh: function(frm) {
        if(frm.doc.__islocal != 1 && frm.doc.docstatus === 0){
            frm.add_custom_button(__("Get Employees"), function(){
                frappe.call({
                    doc: frm.doc,
                    method: "get_employees",
                    callback: function(r) {
                        frm.refresh_field("employees");
                    }
                })
            });
            
        }
        if(frm.doc.docstatus===1){
            frm.add_custom_button(__("Submit Attendance Management"), function(){
                frappe.call({
                    doc: frm.doc,
                    method: "submit_all_attendance_managements",
                    callback: function(r) {
                        if (r.message) {
                            console.log("Success");
                        }
                    }
                })
            })
        }
	},
});
