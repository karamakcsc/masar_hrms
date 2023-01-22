// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Type', {
	// refresh: function(frm) {

	// }
});


////// Fetching Leave Type with Filter ///// Start ///Siam

cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"is_overtime_applicable": 1
		}
	}
}
////// Fetching Leave Type with Filter ///// END ///Siam
