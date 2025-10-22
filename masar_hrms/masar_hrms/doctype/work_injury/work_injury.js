// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Work Injury", {
	injury_start_date: function(frm) {
        frappe.call({
            doc: frm.doc,
            method: "set_end_date",
            callback: function(r) {
                frm.refresh_field("injuries");
            }
        })
	},
    refresh: function(frm) {
        cannot_delete_table_row(frm);
        set_totals(frm);
    }
});

frappe.ui.form.on("Work Injury Detail", {
	no_of_days: function(frm, cdt, cdn) {
        frappe.call({
            doc: frm.doc,
            method: "set_num_of_days_total",
            callback: function(r) {
                frm.refresh_field("total_days");
            }
        })
        frappe.call({
            doc: frm.doc,
            method: "set_end_date",
            callback: function(r) {
                frm.refresh_field("injuries");
            }
        })
	},
    cost_of_treatment: function(frm, cdt, cdn) {
        frappe.call({
            doc: frm.doc,
            method: "set_cost_total",
            callback: function(r) {
                frm.refresh_field("total_cost_of_treatment");
            }
        })
    },
});

function cannot_delete_table_row(frm) {
    frm.doc.injuries.forEach(row => {
        if (row.is_calc === 1) {
            frm.set_df_property("injuries", "cannot_delete_rows", true);
        } else {
            frm.set_df_property("injuries", "cannot_delete_rows", false);
        }
    });
}

function set_totals(frm) {
    frappe.call({
            doc: frm.doc,
            method: "set_totals",
            callback: function(r) {
                frm.refresh_field("total_days");
                frm.refresh_field("total_cost_of_treatment");
            }
        })
}