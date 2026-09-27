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
        frm.toggle_display("bank_name", false);
    },
});
frappe.ui.form.on('Employee External Work History', {
    custom_from_date: function(frm, cdt, cdn) {
        update_total_experience(frm, cdt, cdn);
    },
    custom_to_date: function(frm, cdt, cdn) {
        update_total_experience(frm, cdt, cdn);
    }
});

function update_total_experience(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    if (row.custom_from_date && row.custom_to_date) {
        let from_date = new Date(row.custom_from_date);
        let to_date = new Date(row.custom_to_date);
        let months = (to_date.getFullYear() - from_date.getFullYear()) * 12;
        months += to_date.getMonth() - from_date.getMonth();
        row.total_experience = months;
        frm.refresh_field("external_work_history");
    }
}