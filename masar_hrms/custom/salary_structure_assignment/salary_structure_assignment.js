frappe.ui.form.on("Salary Structure Assignment","base", function(frm) {
    if(frm.doc.change_basic_amount == 1){
    
    frm.set_value("new_basic",frm.doc.base);
    frm.doc.old_basic = flt(frm.doc.new_basic - frm.doc.change_amount);
        // cur_frm.save();
        cur_frm.refresh_field();
        show_alert("Prices are changed",5);
    }
});

frappe.ui.form.on("Salary Structure Assignment","refresh", function(frm) {
    frm.set_df_property("old_basic", "read_only", frm.is_new() ? 0 : 1);
    frm.set_df_property("new_basic", "read_only", frm.is_new() ? 0 : 1);
    frm.set_df_property("change_amount", "read_only", frm.is_new() ? 0 : 1);
    frm.set_df_property("change_to_date", "read_only", frm.is_new() ? 0 : 1);
    frm.set_df_property("change_from_date", "read_only", frm.is_new() ? 0 : 1);
    frm.set_df_property("remark", "read_only", frm.is_new() ? 0 : 1);
});