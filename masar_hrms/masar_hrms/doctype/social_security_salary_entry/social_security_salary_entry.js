// // Copyright (c) 2023, KCSC and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Social Security Salary Entry', {
// 	onload: function (frm) {
// 		if (!frm.doc.posting_date) {
// 			frm.doc.posting_date = frappe.datetime.nowdate();
// 		}
// 		frm.events.department_filters(frm);	
// 	},
// 	department_filters: function (frm) {
// 		frm.set_query("department", function () {
// 			return {
// 				"filters": {
// 					"company": frm.doc.company,
// 				}
// 			};
// 		});
// 	},
// 	refresh: function (frm) {
// 		if (frm.doc.docstatus === 0 && !frm.is_new()) {
// 			frm.page.clear_primary_action();
// 			frm.add_custom_button(__("Get Employees"),
// 				function() {
// 					frm.events.get_employee_details(frm);
// 				}
// 			).toggleClass("btn-primary", !(frm.doc.employees || []).length);
// 		}
// 		if (
// 			(frm.doc.employees || []).length
// 			&& !frappe.model.has_workflow(frm.doctype)
// 			&& !cint(frm.doc.salary_slips_created)
// 			&& (frm.doc.docstatus != 2)
// 		) {
// 			if (frm.doc.docstatus == 0) {
// 				frm.page.clear_primary_action();
// 				frm.page.set_primary_action(__("Create Social Security Salary"), () => {
// 					frm.save("Submit").then(() => {
// 						frm.page.clear_primary_action();
// 						frm.refresh();
// 						frm.events.refresh(frm);
// 					});
// 				});
// 			} else if (frm.doc.docstatus == 1 && frm.doc.status == "Failed") {
// 				frm.add_custom_button(__("Create Social Security Salary"), function () {
// 					frm.call("create_social_security_salary", {}, () => {
// 						frm.reload_doc();
// 					});
// 				}).addClass("btn-primary");
// 			}
// 		}

// 		if (frm.doc.docstatus == 1 && frm.doc.status == "Submitted") {
// 			if (frm.custom_buttons) frm.clear_custom_buttons();
// 			frm.events.add_context_buttons(frm);
// 		}

// 		if (frm.doc.status == "Failed" && frm.doc.error_message) {
// 			const issue = `<a id="jump_to_error" style="text-decoration: underline;">issue</a>`;
// 			let process = (cint(frm.doc.salary_slips_created)) ? "submission" : "creation";

// 			frm.dashboard.set_headline(
// 				__("Salary Slip {0} failed. You can resolve the {1} and retry {0}.", [process, issue])
// 			);

// 			$("#jump_to_error").on("click", (e) => {
// 				e.preventDefault();
// 				frappe.utils.scroll_to(
// 					frm.get_field("error_message").$wrapper,
// 					true,
// 					30
// 				);
// 			});
// 		}

// 		frappe.realtime.on("completed_salary_slip_creation", function() {
// 			frm.reload_doc();
// 		});

// 		frappe.realtime.on("completed_salary_slip_submission", function() {
// 			frm.reload_doc();
// 		});		
// 	},	
// 	get_employee_details: function (frm) {
// 		frappe.msgprint("Hi")
// 		return frappe.call({
// 			doc: frm.doc,
// 			method: 'fill_employee_details',
// 		}).then(r => {
// 			if (r.docs && r.docs[0].employees) {
// 				frm.employees = r.docs[0].employees;
// 				frm.dirty();
// 				frm.save();
// 				frm.refresh();
// 				if (r.docs[0].validate_attendance) {
// 					render_employee_attendance(frm, r.message);
// 				}
// 				frm.scroll_to_field("employees");
// 			}
// 		});
// 	},	
// 	create_social_security_salary: function (frm) {
// 		frm.call({
// 			doc: frm.doc,
// 			method: "create_social_security_salary",
// 			callback: function () {
// 				frm.reload_doc();
// 				frm.toolbar.refresh();
// 			}
// 		});
// 	},	
	
// 	add_context_buttons: function (frm) {
// 		if (frm.doc.salary_slips_submitted || (frm.doc.__onload && frm.doc.__onload.submitted_ss)) {
// 			frm.events.add_bank_entry_button(frm);
// 		} else if (frm.doc.salary_slips_created && frm.doc.status != 'Queued') {
// 			frm.add_custom_button(__("Submit Salary Slip"), function () {
// 				submit_salary_slip(frm);
// 			}).addClass("btn-primary");
// 		}
// 	},
// 	setup: function (frm) {
// 		frm.add_fetch('company', 'cost_center', 'cost_center');

// 		frm.set_query('employee', 'employees', () => {
// 			let error_fields = [];
// 			let mandatory_fields = ['company',  'start_date', 'end_date'];

// 			let message = __('Mandatory fields required in {0}', [__(frm.doc.doctype)]);

// 			mandatory_fields.forEach(field => {
// 				if (!frm.doc[field]) {
// 					error_fields.push(frappe.unscrub(field));
// 				}
// 			});

// 			if (error_fields && error_fields.length) {
// 				message = message + '<br><br><ul><li>' + error_fields.join('</li><li>') + "</ul>";
// 				frappe.throw({
// 					message: message,
// 					indicator: 'red',
// 					title: __('Missing Fields')
// 				});
// 			}

// 			return {
// 				query: "masar_hrms.doctype.social_security_salary_entry.social_security_salary_entry.employee_query",
// 				filters: frm.events.get_employee_filters(frm)
// 			};
// 		});
// 	},

// 	get_employee_filters: function (frm) {
// 		let filters = {};
// 		let fields = ['company', 'start_date', 'end_date',
// 		'department', 'branch', 'designation'];

// 		fields.forEach(field => {
// 			if (frm.doc[field]) {
// 				filters[field] = frm.doc[field];
// 			}
// 		});

// 		if (frm.doc.employees) {
// 			let employees = frm.doc.employees.filter(d => d.employee).map(d => d.employee);
// 			if (employees && employees.length) {
// 				filters['employees'] = employees;
// 			}
// 		}
// 		return filters;
// 	},

// 	company: function (frm) {
// 		frm.events.clear_employee_table(frm);
// 	},

// 	department: function (frm) {
// 		frm.events.clear_employee_table(frm);
// 	},

// 	designation: function (frm) {
// 		frm.events.clear_employee_table(frm);
// 	},

// 	branch: function (frm) {
// 		frm.events.clear_employee_table(frm);
// 	},

// 	start_date: function (frm) {
// 		if (!in_progress && frm.doc.start_date) {
// 			frm.trigger("set_end_date");
// 		} else {
// 			// reset flag
// 			in_progress = false;
// 		}
// 		frm.events.clear_employee_table(frm);
// 	},



// 	clear_employee_table: function (frm) {
// 		frm.clear_table('employees');
// 		frm.refresh();
// 	},
// });



