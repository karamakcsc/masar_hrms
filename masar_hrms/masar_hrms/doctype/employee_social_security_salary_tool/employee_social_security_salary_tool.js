// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Employee Social Security Salary Tool', {
// 	// refresh: function(frm) {
//
// 	// }
// });
// Start Calculate button
frappe.ui.form.on("Employee Social Security Salary Tool", "refresh", function(frm) {
    frm.add_custom_button(__("Build Social Security Salaries"), function() {
      frappe.call({
          method: 'masar_hrms.masar_hrms.doctype.employee_social_security_salary_tool.employee_social_security_salary_tool.build_social_security_salaries',
          args: {
            posting_date: frm.doc.posting_date,
            employee_share_rate: frm.doc.employee_share_rate,
            branch: frm.doc.branch,
            department: frm.doc.department,
          },
          callback: function(ret) {
            frappe.msgprint("Done")
          },
      });
      // frappe.msgprint("Hello")
 },
 );

});
// END Calculate button
