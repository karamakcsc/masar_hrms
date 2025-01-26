// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt


frappe.ui.form.on("Employee Social Security Salary", {
  employee: function(frm){
    frappe.call({
      doc: frm.doc,
      method:'get_share_persent', 
      callback: function(r){
        frm.refresh_field('employee_share_rate');
        frm.refresh_field('company_share_rate');
        if(r.message){
          frappe.call({
            doc:frm.doc,
            method: 'get_social_security_salary',
            callback: function(r){
              frm.refresh_field('social_security_salary');
              CalculateShareAmount(frm)
            }
          })
        }
      }
    })
  }, 
  social_security_salary: function(frm){
    CalculateShareAmount(frm)
  }
});

function CalculateShareAmount(frm){
  frappe.call({
    doc:frm.doc,
    method:'calculate_share_amount', 
    callback:function(r){
      frm.refresh_field('ss_emp_share_amount');
      frm.refresh_field('ss_company_share_amount');
    }
  })
}
