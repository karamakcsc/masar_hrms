// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on('Social Security Salary Entry', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0){
        frm.add_custom_button(__('Get Employees'), function() {
            FillEmployeeDetails(frm)
        });
		if (frm.doc.docstatus == 0 && !frm.is_new()) {
				frm.page.clear_primary_action();
				frm.page.set_primary_action(__("Create Employee Social Security Salary"), () => {
					frm.save("Submit").then(() => {
						frm.page.clear_primary_action();
						frm.refresh();
					});
				});
            }
        
    }
    if (frm.doc.docstatus === 1 && frm.doc.status != 'Submitted'){
        frm.add_custom_button(__('Submit Employee Social Security Salary'), function() {
            frappe.call({
                doc:frm.doc,
                method: 'submit_esss', 
                callback:function(r){
                    frm.set_value('status', 'Submitted');
                    frm.reload_doc();
                }
            });
            
        });    
    } 
}
});


frappe.ui.form.on('Social Security Employee Detail', {
    employees_add: function(frm) {
        frm.set_value('number_of_employees',frm.doc.employees.length);
        
    }, 
    employees_remove: function(frm) {
        frm.set_value('number_of_employees', frm.doc.employees.length);
        
    }
});

function FillEmployeeDetails(frm){

    frappe.call({
        doc:frm.doc,
        method: 'fill_employee_details',
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

}


