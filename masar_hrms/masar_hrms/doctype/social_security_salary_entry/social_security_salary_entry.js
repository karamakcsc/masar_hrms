// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on('Social Security Salary Entry', {
    employees: function(frm) {
        frm.set_value('number_of_employees', frm.doc.employees.length);
        refresh_field('number_of_employees');
    },
    validate: function(frm) {
        frm.set_value('number_of_employees', frm.doc.employees.length);
        refresh_field('number_of_employees');
    },
    refresh: function(frm) {
        frm.add_custom_button(__('Get Employees'), function() {
            frm.events.get_employee_details(frm);
        });
        
    },
    get_employee_details: function(frm) {
        frappe.call({
            method: 'masar_hrms.masar_hrms.doctype.social_security_salary_entry.social_security_salary_entry.fill_employee_details',
            args: {
                department: frm.doc.department,
                branch: frm.doc.branch,
                designation: frm.doc.designation
            },
            callback: function(r) {
                if (r.message) {
                    frm.doc.employees = [];
                    frm.set_value('number_of_employees', r.message.length);
                    $.each(r.message, function(_i, e) {
                        let entry = frm.add_child('employees');
                        entry.employee = e.name;
                        entry.employee_name = e.employee_name;
                        entry.department = e.department;
                        entry.designation = e.designation;
                    });
                    refresh_field('employees');
                }
            }
        });
    }, 
    on_submit: function(frm) {
        frappe.call({
            method: "masar_hrms.masar_hrms.doctype.social_security_salary_entry.social_security_salary_entry.create_employee_social_security_salary",
            args: {
                name: frm.doc.name,
                posting_date: frm.doc.posting_date
            },
            callback: function(r) {
                frappe.msgprint(r.message);
            }
        });
    }
});



















///// mahmoud code 
// frappe.ui.form.on("Social Security Salary Entry" ,{
// 	// "Create Social Security Salary" : function(){
// 	create_social_security_salary : function() {
// 		frappe.call({
// 			method: "masar_hrms.masar_hrms.doctype.social_security_salary_entry.social_security_salary_entry.",
// 			callback: function () {
// 				frappe.msgprint(r.message)
// 				}
// 		});
// 	}
// });


