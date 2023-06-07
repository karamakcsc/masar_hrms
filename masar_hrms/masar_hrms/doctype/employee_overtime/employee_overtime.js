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

cur_frm.fields_dict['salary_structure_assignment'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1,
			"employee": doc.employee
		}
	}
}

// frappe.ui.form.on("Employee Overtime", {
// 	reresh: function(frm){
//   rate_wd(frm);
// 	},
// 	overtime_hours_working_day: function(frm){
// 		rate_wd(frm);
// 	}

// });

// var rate_wd = function(frm) {
//   var doc = frm.doc
//     frm.set_value("rate_hours_working_day",doc.basic_salary / 240 * doc.overtime_rate_working_hour)
// }

// frappe.ui.form.on("Employee Overtime", {
// 	reresh: function(frm){
//   rate_off_day(frm);
// 	},
// 	overtime_hours_off_day: function(frm){
// 		rate_off_day(frm);
// 	}

// });

// var rate_off_day = function(frm) {
//   var doc = frm.doc
//     frm.set_value("rate_hours_off_day",doc.basic_salary / 240 * doc.overtime_rate_off_day)
// }

// frappe.ui.form.on("Employee Overtime", {
// 	rate_hours_working_day: function(frm){
//   amount_wd(frm);
// 	},
// 	overtime_hours_working_day: function(frm){
// 		amount_wd(frm);
// 	}

// });

// var amount_wd = function(frm) {
//   var doc = frm.doc
//     frm.set_value("amount_working_day",doc.rate_hours_working_day * doc.overtime_hours_working_day)
// }

// frappe.ui.form.on("Employee Overtime", {
// 	rate_hours_off_day: function(frm){
//   amount_off_day(frm);
// 	},
// 	overtime_hours_off_day: function(frm){
// 		amount_off_day(frm);
// 	}
// });

// var amount_off_day = function(frm) {
//   var doc = frm.doc
//     frm.set_value("amount_off_day",doc.rate_hours_off_day * doc.overtime_hours_off_day)
// }

// frappe.ui.form.on("Employee Overtime", {
// 	overtime_hours_working_day: function(frm){
//   calculate_total(frm);
// 	},
// 	overtime_hours_off_day: function(frm){
// 		calculate_total(frm);
// 	}
// });

// var calculate_total = function(frm) {
//   var doc = frm.doc
//     frm.set_value("total_amount",doc.amount_working_day + doc.amount_off_day)
// }



frappe.ui.form.on("Employee Overtime", {
    refresh: function(frm) {
        rate_wd(frm);
        rate_off_day(frm);
    },
    overtime_hours_working_day: function(frm) {
        rate_wd(frm);
        amount_wd(frm);
        calculate_total(frm);
    },
    overtime_hours_off_day: function(frm) {
        rate_off_day(frm);
        amount_off_day(frm);
        calculate_total(frm);
    }
});

var rate_wd = function(frm) {
    var doc = frm.doc;
    frm.set_value("rate_hours_working_day", doc.basic_salary / 240 * doc.overtime_rate_working_hour);
};

var rate_off_day = function(frm) {
    var doc = frm.doc;
    frm.set_value("rate_hours_off_day", doc.basic_salary / 240 * doc.overtime_rate_off_day);
};

var amount_wd = function(frm) {
    var doc = frm.doc;
    frm.set_value("amount_working_day", doc.rate_hours_working_day * doc.overtime_hours_working_day);
};

var amount_off_day = function(frm) {
    var doc = frm.doc;
    frm.set_value("amount_off_day", doc.rate_hours_off_day * doc.overtime_hours_off_day);
};

var calculate_total = function(frm) {
    var doc = frm.doc;
    frm.set_value("total_amount", flt(doc.amount_working_day) + flt(doc.amount_off_day));
};
