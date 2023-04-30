frappe.ui.form.on('Employee',  {
    refresh: function(frm) {
        var total = 0;
        $.each(frm.doc.family_members,  function(i,  d) {
         var date1 = d.birth_date;
         var date2 = frappe.datetime.get_today();
         var yearsDiff =  frappe.datetime.get_day_diff(date2, date1 ) / 365;
         if(((d.relative_relation == "Son" & yearsDiff < 18) || d.relative_relation == "Daughter") ) total = total + 1;
        });
        frm.set_value("children_subject_to_allowance",total);
    }

});

frappe.ui.form.on("Employee","refresh", function(frm) {
    // frm.toggle_display("naming_series", false);
    //frm.toggle_display("is_pos", false);
    frm.toggle_display("bank_name", false);
});
