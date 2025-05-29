// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt


frappe.ui.form.on('Attendance Shortage Processing', {
    employee: function(frm) {
        GetBasicSalary(frm);
    },
    onload: function(frm){
        GetBasicSalary(frm);
    },
    refresh: function(frm) {
        GetBasicSalary(frm);
    }
});



cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"type": "Deduction"
		}
	}
}


function GetBasicSalary(frm){
    if (frm.doc.employee){
    frappe.call({
        method:'masar_hrms.masar_hrms.doctype.employee_overtime.employee_overtime.get_basic_salary', 
        args: 
        {
            employee: frm.doc.employee, 
            company: frm.doc.company
        }, 
        callback:function(r){
            frm.set_value('basic_salary', r.message);
            frm.refresh_field('basic_salary');
        }
    }); 
    }else { 
        frm.set_value('basic_salary', null);
        frm.refresh_field('basic_salary');
    }
}