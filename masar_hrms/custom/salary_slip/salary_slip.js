
// /////// form mahmoud to company ss 

frappe.ui.form.on("Salary Slip", {
    on_submit: function(frm) {
        frappe.call({
          method: "masar_hrms.custom.salary_slip.salary_slip.ss_jv",
          args:{
            name : frm.doc.name, 
            employee : frm.doc.employee,
            posting_date : frm.doc.posting_date , 
            payroll_entry : frm.doc.payroll_entry 
          },
          callback: function(r) {   
            frappe.msgprint(r.message);   
          }
        });    
     }
    });

