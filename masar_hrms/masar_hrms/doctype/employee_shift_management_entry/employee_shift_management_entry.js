// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on('Employee Shift Management Entry', {
    refresh: function (frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			// frm.page.clear_primary_action();
			frm.add_custom_button(__("Get Employees"),
				function() {
					frm.events.get_employee_details(frm);
				}
			)
		}
	},
	on_submit : function (frm){
		frappe.call({
			
			method: 'masar_hrms.masar_hrms.doctype.employee_shift_management_entry.employee_shift_management_entry.create_esm',
			args:{
				doc: frm.doc.name , 
				posting_date :frm.doc.posting_date , 
				status : frm.doc.status , 
				end_date : frm.doc.end_date , 
				start_date : frm.doc.start_date , 
				saturday_st : frm.doc.saturday_st , 
				wednesday_st : frm.doc.wednesday_st , 
				sunday_st : frm.doc.sunday_st , 
				thursday_st : frm.doc.thursday_st , 
				monday_st : frm.doc.monday_st , 
				friday_st : frm.doc.friday_st , 
				tuesday_st :frm.doc.tuesday_st , 
			}, 
			callback: function(r){
				frappe.msgprint(r.message);
			}

		});
	},
	get_employee_details: function (frm) {
		frappe.call({
			
			method: 'masar_hrms.masar_hrms.doctype.employee_shift_management_entry.employee_shift_management_entry.fill_employee_details',
			args:{
				doc: frm.doc.name,
				department :frm.doc.department,
			}	
		}).done((r) => {
			console.log(r)
			frm.doc.employee_table = []
			frm.set_value('number_of_employees' , r.message.length) // doc.number_of_employees = r.message.length;
			$.each(r.message , function (_i ,e){
				let entry = frm.add_child("employee_table");
				entry.employee = e.name;
				entry.employee_name = e.employee_name ; 
				entry.department = e.department;
			}) 
			refresh_field("employee_table")
		})
	}
});
