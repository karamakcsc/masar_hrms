// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Shift Management", {
	refresh:function(frm) {
        ShiftsPeriodButton(frm);
	},        
    saturday_st :function(frm) {
        ShiftsPeriodButton(frm);
	},      
    sunday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    sunday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    monday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    tuesday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    wednesday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    thursday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    friday_st:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    start_date:function(frm) {
        ShiftsPeriodButton(frm);
	},      
    end_date:function(frm) {
        ShiftsPeriodButton(frm);
	},      
});

frappe.ui.form.on("Shift Management Period", {
    shift_date: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn]; 
        frappe.call({
            doc:frm.doc,
            method:'get_day_by_date', 
            args : {
                date: row.shift_date
            }, 
            callback:function(r) { 
                frappe.model.set_value(cdt , cdn , 'shift_day' , r.message);
            }
        });
    }
});

function ShiftsPeriodButton(frm) {
    const required_fields = [
        'saturday_st',
        'sunday_st',
        'monday_st',
        'tuesday_st',
        'wednesday_st',
        'thursday_st',
        'friday_st',
        'start_date',
        'end_date'
    ];
    const all_filled = required_fields.every(field => frm.doc[field]);
    if (all_filled && frm.doc.docstatus === 0) {
        frm.add_custom_button(__("Shifts Period"), function () {
            frappe.call({
                doc: frm.doc,
                method: 'insert_shifts_periods',
                callback: function (r) {
                    frm.refresh_field('shifts_period');
                }
            });
        }, __("Insert"));
    }
}

