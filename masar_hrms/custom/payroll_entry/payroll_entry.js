

frappe.ui.form.on('Payroll Entry', {
  refresh: function(frm) {
    if (frappe.user.has_role('Accounts Manager')  && (frm.doc.docstatus == 1)){
      frm.add_custom_button(('Social Security JV'), function () {
        frappe.call({
          method: "masar_hrms.custom.payroll_entry.payroll_entry.check_ss_jv",
          args:{                
              company : frm.doc.company,
              name  : frm.doc.name,
              posting_date : frm.doc.posting_date , 
              cost_center : frm.doc.cost_center 
            },
          callback: function(r) {   
            frappe.msgprint(r.message);   
            }
        });  
      }); 
    }
  },
});







