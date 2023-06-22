// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Short Leave Application', {
	// refresh: function(frm) {

	// }
});


function timeToMins(time) {
  var b = time.split(':');
  return b[0]*60 + +b[1];
}

// Convert minutes to a time in format hh:mm
// Returned value is in range 00  to 24 hrs
function timeFromMins(mins) {
  function z(n){return (n<10? '0':'') + n;}
  var h = (mins/60 |0) % 24;
  var m = mins % 60;
  return z(h) + ':' + z(m);
}

// Add two times in hh:mm format
function addTimes(t0, t1) {
  return timeFromMins(timeToMins(t0) + timeToMins(t1));
}


//// Fetching Data ///// Start ///Siam
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');
cur_frm.add_fetch('employee', 'company', 'company');
//// Fetching Data ///// END ///Siam

////// Fetching Leave Type with Filter ///// Start ///Siam

cur_frm.fields_dict['leave_type'].get_query = function(doc) {
	return {
		filters: {
			"is_short_leave": 1
		}
	}
}
cur_frm.fields_dict['salary_structure_assignment'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1,
			"employee": doc.employee
		}
	}
}

cur_frm.fields_dict['salary_component'].get_query = function(doc) {
	return {
		filters: {
			"type": "Deduction"
		}
	}
}

////// Fetching Leave Type with Filter ///// END ///Siam





frappe.ui.form.on("Short Leave Application", {
	setup: function(frm) {
		frm.set_query("leave_approver", function() {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype
				}
			};
		});

		frm.set_query("employee", erpnext.queries.employee);
	},
	onload: function(frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];

		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.toggle_reqd("leave_approver", true);
					}
				}
			});
		}
	},

	refresh: function(frm) {
		if (frm.is_new()) {
			frm.trigger("calculate_total_days");
		}
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !in_list(frappe.user_roles, "Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		if (!frm.doc.employee && frappe.defaults.get_user_permissions()) {
			const perm = frappe.defaults.get_user_permissions();
			if (perm && perm['Employee']) {
				frm.set_value('employee', perm['Employee'].map(perm_doc => perm_doc.doc)[0]);
			}
		}
	},

	employee: function(frm) {
	 	frm.trigger("get_leave_balance");
		frm.trigger("get_working_hours");
		frm.trigger("set_leave_approver");
	},

	leave_approver: function(frm) {
		if (frm.doc.leave_approver) {
			frm.set_value("leave_approver_name", frappe.user.full_name(frm.doc.leave_approver));
		}
	},

	leave_type: function(frm) {
		frm.trigger("get_leave_balance");
		frm.trigger("get_working_hours");
	},

	leave_duration: function(frm){
		frm.doc.total_leave_hours = frm.doc.leave_duration / 3600
		var from_time = frm.doc.from_time;
			frappe.call({
			method: "masar_hrms.masar_hrms.doctype.short_leave_application.short_leave_application.calculate_to_time",
			args: {
				"from_time": frm.doc.from_time,
				"total_leave_hours": frm.doc.leave_duration
			},
			callback: function(r) {
				frm.doc.to_time = r.message;
				frm.refresh_field("to_time");
			}
		});

			
		// frm.set_value('to_time',to_time)
		// frm.refresh_field('to_time')
		// var duration = cur_frm.doc.total_leave_hours.toString();
		// var from_time = cur_frm.doc.from_time;
		// var hour=0;
		// var minute=0;
		// var second=0;
		// // var split_duration= duration.split(':');
		// var split_from_time= from_time.split(':');
		// hour = parseInt(duration/3600)+parseInt(split_from_time[0]);
		// duration=duration%3600
		// minute = parseInt(duration/60)+parseInt(split_from_time[1]);
		// hour = hour + minute/60;
		// minute = minute%60;
		// duration=duration%60
		// second = parseInt(duration)+parseInt(split_from_time[2]);
		// minute = minute + second/60;
		// second = second%60;
		// cur_frm.set_value('to_time',parseInt(hour)+':'+parseInt(minute)+':'+parseInt(second))
		// cur_frm.refresh_fields('to_time')
		// frm.doc.to_time=addTimes(frm.doc.from_time, frm.doc.total_leave_hours)
		// refresh_field("to_time");
	},

	from_date: function(frm) {
		frm.trigger("calculate_total_days");
	},

	to_date: function(frm) {
		frm.trigger("calculate_total_days");
	},

	get_leave_balance: function(frm) {

		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.posting_date && frm.doc.posting_date) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
				args: {
					employee: frm.doc.employee,
					date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					leave_type: frm.doc.leave_type,
					consider_all_leaves_in_the_allocation_period: 1
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.set_value('leave_balance', r.message);
						frm.set_value('leave_balance_hr', r.message *8);
					} else {
						frm.set_value('leave_balance', "0");
						frm.set_value('leave_balance_hr', "0");
					}
				}
			});
		}
	},

	get_working_hours: function(frm) {

		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.posting_date && frm.doc.posting_date) {
			return frappe.call({
				method: "masar_hrms.masar_hrms.doctype.short_leave_application.short_leave_application.calculate_working_hours",
				args: {
					"employee": frm.doc.employee,
					"posting_date": frm.doc.posting_date
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.set_value('working_hours', r.message);
					} else {
						frm.set_value('working_hours', "0");
					}
				}
			});
		}
	},

	calculate_total_days: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type) {

			var from_date = Date.parse(frm.doc.from_date);
			var to_date = Date.parse(frm.doc.to_date);

			if (to_date < from_date) {
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value('to_date', '');
				return;
			}
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
				args: {
					"employee": frm.doc.employee,
					"leave_type": frm.doc.leave_type,
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"half_day": frm.doc.half_day,
					"half_day_date": frm.doc.half_day_date,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('total_leave_days', r.message);
						frm.trigger("get_leave_balance");
						frm.trigger("get_working_hours");
					}
				}
			});
		}
	},

	set_leave_approver: function(frm) {
		if (frm.doc.employee) {
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'hrms.hr.doctype.leave_application.leave_application.get_leave_approver',
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('leave_approver', r.message);
					}
				}
			});
		}
	}
});
