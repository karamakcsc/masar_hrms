// // Copyright (c) 2023, KCSC and contributors
// // For license information, please see license.txt

frappe.ui.form.on("Short Leave Application", {
	employee: function(frm){
        if (frm.doc.employee){
        frm.set_query("shift_assignment", function () {
            return {
                filters: {
                    employee: frm.doc.employee,
                    status: 'Active'
                    },
                };
            });
        }
    }, 
    shift_start:function(frm){
        GetStartEndShift(frm);
    },
    end_shift:function(frm){
        GetStartEndShift(frm);
    },
    in_shift:function(frm){
        GetStartEndShift(frm);
    }, 
    leave_duration:function(frm){
        CalculateDuration(frm);
    },
    onload: function(frm) {
        DocFilters(frm);
	},
    refresh: function(frm){
        DocFilters(frm);
    },
    leave_type: function(frm){
        get_leave_balance(frm);
    },
});
function GetStartEndShift(frm){
    frappe.call({
        doc:frm.doc,
        method:'get_start_end_shift',
        callback: function(r) {
            frm.doc.to_time=r.message.to_time;
            frm.doc.from_time = r.message.from_time;
            refresh_field("from_time");
            refresh_field("to_time");
        }
    });
}
function CalculateDuration(frm){
    frappe.call({
        doc:frm.doc,
        method:'calculate_durations',
        callback: function(r) {
            if (r.message.from_time) {
                frm.doc.from_time = r.message.from_time;
                refresh_field("from_time");
            }
            if (r.message.to_time) {
                frm.doc.to_time = r.message.to_time;
                refresh_field("to_time");
            }
        }
    })
}
function  DocFilters(frm){
    frm.set_query("salary_component", function () {
        return {
            filters: {
                type: 'Deduction'
            },
        };
    });
}

function get_leave_balance(frm){
    if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.leave_date && frm.doc.leave_date) {
        return frappe.call({
            method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
            args: {
                employee: frm.doc.employee,
                date: frm.doc.posting_date,
                to_date: frm.doc.posting_date,
                leave_type: frm.doc.leave_type,
                consider_all_leaves_in_the_allocation_period: 1
            },
            callback: function (r) {
                if (!r.exc && r.message) {
                    frm.set_value('leave_balance', r.message); // leave balance days
                    frm.set_value('leave_balance_hh', r.message *8); // leave balance hours
                } else {
                    frm.set_value('leave_balance', "0");
                    frm.set_value('leave_balance_hh', "0");
                }
            }
        });
    }
}