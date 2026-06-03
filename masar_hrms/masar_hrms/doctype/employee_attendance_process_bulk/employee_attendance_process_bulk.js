// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Attendance Process Bulk", {
	refresh: function(frm) {
		GetStandardDatePeriod(frm);
		setupButtons(frm);
	},
	setup: function(frm) {
		GetStandardDatePeriod(frm);
	},
	onload: function(frm) {
		GetStandardDatePeriod(frm);
	},
	posting_date: function(frm) {
		GetStandardDatePeriod(frm);
	},
});

function setupButtons(frm) {
	// Draft state: Insert Employees + rename primary action to "Create Process"
	if (frm.doc.docstatus === 0) {
		frm.add_custom_button(__("Employees"), function() {
			frappe.call({
				doc: frm.doc,
				method: 'insert_employees',
				callback: function(r) {
					frm.refresh_field('employees');
				}
			});
		}, __("Insert"));

		// Override the default "Submit" label with "Create Process"
		frm.page.set_primary_action(__("Create Process"), function() {
			frm.savesubmit();
		});
	}

	// Submitted state: show Submit All Processes button
	if (frm.doc.docstatus === 1) {
		frm.add_custom_button(__("Submit All Processes"), function() {
			frappe.confirm(
				__("This will submit all draft Attendance Process records linked to this document. Continue?"),
				function() {
					frappe.call({
						doc: frm.doc,
						method: 'submit_all_processes',
						freeze: true,
						freeze_message: __("Submitting processes, please wait…"),
						callback: function(r) {
							frm.reload_doc();
						}
					});
				}
			);
		}, __("Actions"));
	}
}

function GetStandardDatePeriod(frm) {
	if (!frm.doc.from_date && !frm.doc.to_date) {
		frappe.call({
			doc: frm.doc,
			method: 'get_standard_date_period',
			callback: function(r) {
				if (r.message) {
					frm.set_value('from_date', r.message.from_date);
					frm.set_value('to_date', r.message.to_date);
				}
			}
		});
	}
}
