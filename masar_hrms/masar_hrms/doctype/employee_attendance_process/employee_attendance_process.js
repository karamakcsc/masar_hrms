// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on("Employee Attendance Process", {
    employee: function(frm) {
        GetSalaryDetailsForEmployee(frm);
        GetOvertimeTypeAsDefualt(frm)
    },
    posting_date: function(frm) {
        GetStandardDatePeriod(frm);
    },
    refresh: function(frm) {
        GetStandardDatePeriod(frm);
        GetOvertimeTypeAsDefualt(frm)
    },
    setup: function(frm) {
        GetStandardDatePeriod(frm);
        GetOvertimeTypeAsDefualt(frm)
    },
    onload: function(frm) {
        GetStandardDatePeriod(frm);
        GetOvertimeTypeAsDefualt(frm)
    },
});

function GetSalaryDetailsForEmployee(frm) {
    frappe.call({
        doc: frm.doc,
        method: 'get_salary_details',
        args: {
            employee: frm.doc.employee
        },
        callback: function(r) {
            frm.doc.basic_salary = r.message.basic_salary;
            frm.doc.basic_salary_hour_rate = r.message.hour_rate;
            frm.refresh_field('basic_salary');
            frm.refresh_field('basic_salary_hour_rate');
        }
    });
}

function GetStandardDatePeriod(frm) {
    if (!frm.doc.from_date && !frm.doc.to_date) {
        frappe.call({
            doc: frm.doc,
            method: 'get_standard_date_period',
            callback: function(r) {
                frm.doc.from_date = r.message.from_date;
                frm.doc.to_date = r.message.to_date;
                frm.refresh_field('from_date');
                frm.refresh_field('to_date');
            }
        });
    }
}
function GetOvertimeTypeAsDefualt(frm){ 
    frappe.call({
        doc:frm.doc ,  
        method: 'get_overtime_type_as_defualt', 
        callback: function(r){ 
            if(!frm.doc.ot_wd) {
                frm.doc.ot_wd = r.message.wd_type;
                frm.refresh_field('ot_wd');
                frm.refresh_field('ot_wd_rate');
                frm.refresh_field('salary_component_wd');
            }
            if(!frm.doc.ot_od) {
                frm.doc.ot_od = r.message.od_type;
                frm.refresh_field('ot_od');
                frm.refresh_field('ot_od_rate');
                frm.refresh_field('salary_component_od');
            }
        }
    })
}
