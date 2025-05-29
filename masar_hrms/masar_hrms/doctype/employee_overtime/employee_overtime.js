// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Employee Overtime', {
// 	// refresh: function(frm) {

// 	// }
// });


cur_frm.fields_dict['employee'].get_query = function(doc) {
	return {
		filters: {
			"is_overtime_applicable": 1
		}
	}
}

cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"is_overtime_applicable": 1
		}
	}
}



frappe.ui.form.on("Employee Overtime", {
    // refresh: function(frm) {
    //     if(frm.doc.docstatus !=1){
    //     rate_wd(frm);
    //     rate_off_day(frm);
    //     }
    // },
    overtime_hours_working_day: function(frm) {
        if(frm.doc.docstatus !=1){
        rate_wd(frm);
        amount_wd(frm);
        calculate_total(frm);
        }
    },
    overtime_hours_off_day: function(frm) {
        if(frm.doc.docstatus !=1){
        rate_off_day(frm);
        amount_off_day(frm);
        calculate_total(frm);
        }
    },
    validate: function(frm) {
        if(frm.doc.docstatus !=1){
        rate_off_day(frm);
        amount_off_day(frm);
        calculate_total(frm);
        }
        GetBasicSalary(frm);
    },
    // setup: function(frm) {
    //     if(frm.doc.docstatus !=1){
    //     rate_off_day(frm);
    //     amount_off_day(frm);
    //     calculate_total(frm);
    //     }
    // },
    on_submit: function(frm) {
        if(frm.doc.docstatus !=1){
        rate_off_day(frm);
        amount_off_day(frm);
        calculate_total(frm);
    }
    } ,
    employee: function(frm){
        GetBasicSalary(frm);
    }
});
var rate_wd = function(frm) {
    var doc = frm.doc;
    if (doc.basic_salary && doc.overtime_rate_working_hour) {
        frm.set_value("rate_hours_working_day", flt(doc.basic_salary / 240 * doc.overtime_rate_working_hour));
        frm.refresh_field('rate_hours_working_day');
    }
};

var rate_off_day = function(frm) {
    var doc = frm.doc;
    if (doc.basic_salary && doc.overtime_rate_off_day) {
        frm.set_value("rate_hours_off_day", flt(doc.basic_salary / 240 * doc.overtime_rate_off_day));
        frm.refresh_field('rate_hours_off_day');
    }
};

var amount_wd = function(frm) {
    var doc = frm.doc;
    if (doc.rate_hours_working_day && doc.overtime_hours_working_day) {
        frm.set_value("amount_working_day", flt(doc.rate_hours_working_day * doc.overtime_hours_working_day));
        frm.refresh_field('amount_working_day');
    }
};

var amount_off_day = function(frm) {
    var doc = frm.doc;
    if (doc.rate_hours_off_day && doc.overtime_hours_off_day) {
        frm.set_value("amount_off_day", flt(doc.rate_hours_off_day * doc.overtime_hours_off_day));
        frm.refresh_field('amount_off_day');
    }
};

var calculate_total = function(frm) {
    var doc = frm.doc;
    if (doc.amount_working_day && doc.amount_off_day) {
        frm.set_value("total_amount", flt(doc.amount_working_day) + flt(doc.amount_off_day));
        frm.refresh_field('total_amount');
    }
};


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