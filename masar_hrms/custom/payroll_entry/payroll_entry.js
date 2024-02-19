

frappe.ui.form.on('Payroll Entry', {
  refresh: function(frm) {
    if (frappe.user.has_role('Accounts Manager') && (frm.doc.docstatus == 1)) {
      frm.add_custom_button(('Social Security JV'), function () {
        frappe.call({
          method: "masar_hrms.custom.payroll_entry.payroll_entry.check_ss_jv",
          args:{                
              company : frm.doc.company,
              name  : frm.doc.name,
              posting_date : frm.doc.posting_date
            },
          callback: function(r) {   
            frappe.msgprint(r.message);   
          }
        });  
      }); 
    }

    // Hide the button when docstatus is 0 or 2
    frm.toggle_display('Social Security JV', frm.doc.docstatus != 0 && frm.doc.docstatus != 2);
  },
});

