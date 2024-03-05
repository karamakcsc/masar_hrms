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
    frm.toggle_display("bank_name", false);
});



frappe.ui.form.on('Employee' , {
    validate : function(frm){
        frappe.call({
            method : "masar_hrms.custom.employee.employee.employee_full_name" , 
            args:{
                name : frm.doc.name
            }, 
            callback: function(r){
                frm.set_value('employee_name', r.message.full_name_en);
                frm.set_value('full_name_ar', r.message.full_name_ar);
            }
        }); 

    }
});