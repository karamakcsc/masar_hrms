// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Component Management", {
	employee:function(frm) {
        frappe.call({
            doc:frm.doc, 
            method:'get_exist_setting_from_employee', 
            args:{
                employee : frm.doc.employee
            },
            callback:function(r){
                frm.refresh_fields();
            }
        })
	},
    social_security_salary: function(frm) {
        frappe.call({
            doc:frm.doc, 
            method:'calculate_salry_details_section', 
            callback:function(r){
                frm.refresh_fields();
            }
        })
    }, 
    edit_ss_salary: function(frm) {
        frappe.call({
            doc:frm.doc, 
            method:'calculate_salry_details_section', 
            callback:function(r){
                frm.refresh_fields();
            }
        })
    }, 
});
