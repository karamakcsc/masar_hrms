// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Social Security Salary', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Employee Social Security Salary", "employee", function(frm) {
    frm.doc.employee_share_rate=frappe.model.get_doc("Company", frm.doc.company).employee_share_rate
    frm.doc.company_share_rate=frappe.model.get_doc("Company", frm.doc.company).company_share_rate
    // employee_doc=frappe.model.get_doc("Employee", frm.doc.employee)
		if(frappe.model.get_doc("Employee", frm.doc.employee).is_social_security_applicable==false){
			frappe.throw(frm.doc.employee + " is not applicable in social security")
    }
		// calculate_social_security_amount(self)
    frappe.call({
        method: 'masar_hr.masar_hr.doctype.employee_social_security_salary.employee_social_security_salary.calculate_social_security_amount',
        args: {
          posting_date: frm.doc.posting_date,
          employee: frm.doc.employee,
        },
        callback: function(ret) {
          frm.doc.amount=ret.message
          frappe.msgprint("Done")
        },
    });
});
