// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Social Security Salary", {
  validate: function(frm) {
      frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Employee",
            name: frm.doc.employee
        },
        callback: function (r) {
            if(r.message) {
              if(r.message.is_social_security_applicable==false){
                frappe.msgprint(__(frm.doc.employee + " is not applicable in social security"));
                validated = false;
              }
            else {
              var company_share= 0.0
              var emp_share= 0.0
              company_share= frm.doc.amount * frm.doc.company_share_rate / 100
              emp_share= frm.doc.amount * frm.doc.employee_share_rate / 100
              
              frm.set_value("ss_company_share_amount",company_share);
              frm.set_value("ss_emp_share_amount",emp_share);
              
            }  
    
            }
        }
    });
   
  }
});

frappe.ui.form.on("Employee Social Security Salary", "employee", function(frm) {
    // Get Share rate from company  
    frappe.call({
      method: "frappe.client.get",
      args: {
          doctype: "Company",
          name: frm.doc.company
      },
      callback: function (r) {
          if(r.message) {
            frm.doc.employee_share_rate= r.message.employee_share_rate
            frm.doc.company_share_rate=r.message.company_share_rate
          }
      }
  });

});

frappe.ui.form.on('Employee Social Security Salary', {
  refresh: function(frm) {
      frm.add_custom_button(__("Calculate Social Security Salary"), function() {
        frappe.call({
          method: "frappe.client.get",
          args: {
              doctype: "Employee",
              name: frm.doc.employee
          },
          callback: function (r) {
              if(r.message) {
                if(r.message.is_social_security_applicable==false){
                  frappe.throw(frm.doc.employee + " is not applicable in social security")
                }
                frappe.call({
                  method: 'calculate_social_security_amount',
                  doc: frm.doc,
                  // args: {
                  //   posting_date: frm.doc.posting_date,
                  //   employee: frm.doc.employee,
                  // },
                  callback: function(ret) {
                    frm.set_value("amount",ret.message);
                    frappe.msgprint(ret.message.toString())
                  },
              });
              }
          }
      });
      }, "fa fa-plus", "btn-primary");
  }
});