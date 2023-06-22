// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Shortage', {
	// refresh: function(frm) {

	// }
});


frappe.ui.form.on("Attendance Shortage", "refresh", function(frm) {
    frm.add_custom_button(__("Deduct From Salary"), function() {
        frappe.msgprint("Button clicked!");
    });
});



cur_frm.fields_dict['short_leave_application'].get_query = function(doc) {
    var attendanceDate = frappe.datetime.str_to_obj(doc.attendance_date);
    var startOfMonth = new Date(attendanceDate.getFullYear(), attendanceDate.getMonth(), 1);
    var endOfMonth = new Date(attendanceDate.getFullYear(), attendanceDate.getMonth() + 1, 0);

    return {
        filters: {
            "docstatus": 1,
            "employee": doc.employee,
            "posting_date": ["between", [
                frappe.datetime.obj_to_str(startOfMonth, "yyyy-mm-dd"),
                frappe.datetime.obj_to_str(endOfMonth, "yyyy-mm-dd")
            ]]
        }
    };
};



cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"type": "Deduction"
		}
	}
}



frappe.ui.form.on('Attendance Shortage', {
    onload: function(frm) {
            frappe.call({
                method: "masar_hrms.masar_hrms.doctype.attendance_shortage.attendance_shortage.get_salary_structure_assignment",
                args: {
                    employee: frm.doc.employee
                },
                callback: function(r) {
                    if (r && r.message) {
                        frm.set_value('salary_structure_assignment', r.message);
                    } else {
                        frappe.msgprint("This Employee Don't Have Salary Structure Assignment.");
                    }
                }
            });
    }
});