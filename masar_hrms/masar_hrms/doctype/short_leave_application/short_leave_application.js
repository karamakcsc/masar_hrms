// // Copyright (c) 2023, KCSC and contributors
// // For license information, please see license.txt

frappe.ui.form.on("Short Leave Application", {
	employee: function(frm){
       GetShiftAssignmentActive(frm);
    }, 
    // shift_start:function(frm){
    //     GetStartEndShift(frm);
    // },
    // end_shift:function(frm){
    //     GetStartEndShift(frm);
    // },
    // in_shift:function(frm){
    //     GetStartEndShift(frm);
    // }, 
    // leave_duration:function(frm){
    //     CalculateDuration(frm);
    // },
    leave_date: function(frm){
        GetShiftAssignmentActive(frm);
        // get_leave_balance(frm);
    },
    leave_type: function(frm){
        GetLeaveBalance(frm);
    },
    leave_duration: function(frm){
        GetToTime(frm);
    }
});
// function GetStartEndShift(frm){
//     frappe.call({
//         doc:frm.doc,
//         method:'get_start_end_shift',
//         callback: function(r) {
//             frm.doc.to_time=r.message.to_time;
//             frm.doc.from_time = r.message.from_time;
//             refresh_field("from_time");
//             refresh_field("to_time");
//         }
//     });
// }
// function CalculateDuration(frm){
//     frappe.call({
//         doc:frm.doc,
//         method:'calculate_durations',
//         callback: function(r) {
//             if (r.message.from_time) {
//                 frm.doc.from_time = r.message.from_time;
//                 refresh_field("from_time");
//             }
//             if (r.message.to_time) {
//                 frm.doc.to_time = r.message.to_time;
//                 refresh_field("to_time");
//             }
//         }
//     })
// }


// function get_leave_balance(frm){
//     if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.leave_date && frm.doc.leave_date) {
//         return frappe.call({
//             method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
//             args: {
//                 employee: frm.doc.employee,
//                 date: frm.doc.posting_date,
//                 to_date: frm.doc.posting_date,
//                 leave_type: frm.doc.leave_type,
//                 consider_all_leaves_in_the_allocation_period: 1
//             },
//             callback: function (r) {
//                 if (!r.exc && r.message) {
//                     frm.set_value('leave_balance', r.message); // leave balance days
//                     frm.set_value('leave_balance_hh', r.message *8); // leave balance hours
//                 } else {
//                     frm.set_value('leave_balance', "0");
//                     frm.set_value('leave_balance_hh', "0");
//                 }
//             }
//         });
//     }
// }

// function getLeaveApprover(frm) {
//     if (frm.doc.employee) {
//         frappe.call({
//             method: "masar_hrms.masar_hrms.doctype.short_leave_application.short_leave_application.get_leave_approver",
//             args: {
//                 employee: frm.doc.employee
//             },
//             callback: function (r) {
//                 if (r.message) {
//                     frm.set_value('leave_approver', r.message);
//                     frm.refresh_field('leave_approver');
//                 }
//             }
//         })
//     }
// }
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