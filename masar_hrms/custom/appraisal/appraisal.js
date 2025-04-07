frappe.ui.form.on('Appraisal', {
    refresh: function(frm) {
        setReadOnly(frm);
    },
    setup: function(frm) {
        setReadOnly(frm);
    },
});


function setReadOnly(frm) {
    if (frappe.user.has_role("Employee Manager")) {
        frm.set_df_property('self_ratings', 'read_only', 1);
    }
    frm.fields_dict["self_ratings"].grid.update_docfield_property("per_weightage", "read_only", 1);
}
