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
        frm.fields_dict["injuries"].grid.grid_rows.forEach(function(grid_row) {
            let row = grid_row.doc;

            if (row.is_calc) {
                grid_row.toggle_editable(false);
                grid_row.can_delete = false;
            } else {
                grid_row.toggle_editable(true);
                grid_row.can_delete = true;
            }
        });

        frm.fields_dict["injuries"].grid.refresh();
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
    is_calc: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let grid_row = frm.fields_dict["injuries"].grid.get_row(cdn);

        if (row.is_calc) {
            grid_row.toggle_editable(false);
            grid_row.can_delete = false;
        } else {
            grid_row.toggle_editable(true);
            grid_row.can_delete = true;
        }

        frm.fields_dict["injuries"].grid.refresh();
    }
});