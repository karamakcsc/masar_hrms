// // Copyright (c) 2023, KCSC and contributors
// // For license information, please see license.txt

frappe.ui.form.on("Short Leave Application", {
	employee: function(frm){
       GetShiftAssignmentActive(frm);
       GetLeaveSalaryandHourRate(frm);
    }, 
    leave_date: function(frm){
        GetShiftAssignmentActive(frm);
    },
    leave_type: function(frm){
        GetLeaveBalance(frm);
    },
    leave_duration: function(frm){
        GetToTime(frm);
        GetTotalAmountByDuration(frm);
    }, 
    salary_deduction: function(frm){
        GetLeaveSalaryandHourRate(frm);
    }
});
function GetShiftAssignmentActive(frm){
    frappe.call({
        doc:frm.doc, 
        method: 'get_shift_assiggnment_active', 
        callback:function(r){
            if (r.message){
            frm.doc.shift_assignment = r.message.shift_assignment;
            frm.doc.shift_type = r.message.shift_type;
            frm.refresh_field("shift_assignment");
            frm.refresh_field("shift_type");
            }
        }
    })
}
function GetLeaveBalance(frm){
    frappe.call({
        doc:frm.doc,
        method:'get_leave_balance',
        callback: function(r) {
            if (r.message) {
                frm.doc.leave_balance = r.message;
                frm.refresh_field("leave_balance");
            } else {
                frm.doc.leave_balance = 0;
                frm.refresh_field("leave_balance");
            }
        }
    });
}
function GetToTime(frm){
        frappe.call({
            doc:frm.doc,
            method:'get_to_time',
            callback: function(r) {
                if (r.message) {
                    frm.doc.to_time = r.message;
                    frm.refresh_field("to_time");
                } else {
                    frm.doc.to_time = null;
                    frm.refresh_field("to_time");
                }
            }
        });
}
function GetLeaveSalaryandHourRate(frm){
    frappe.call({
        doc:frm.doc,
        method:'get_leave_salary_and_hour_rate',
        callback: function(r) {
            if (r.message) {
                frm.doc.leave_salary = r.message.leave_salary;
                frm.doc.hourly_rate = r.message.hourly_rate;
                frm.refresh_field("leave_salary");
                frm.refresh_field("hourly_rate");
            } else {
                frm.doc.leave_salary = 0;
                frm.doc.hourly_rate = 0;
                frm.refresh_field("leave_salary");
                frm.refresh_field("hourly_rate");
            }
        }
    });
}
function GetTotalAmountByDuration(frm){
    frappe.call({
        doc:frm.doc,
        method:'get_total_amount_by_duration',
        callback: function(r) {
            if (r.message) {
                frm.doc.total_amount = r.message;
                frm.refresh_field("total_amount");
            } else {
                frm.doc.total_amount = 0;
                frm.refresh_field("total_amount");
            }
        }
    });
}