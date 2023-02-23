// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Social Security Salary Entry', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Employee Social Security Salary Entry', {
	onload: function (frm) {
		if (!frm.doc.posting_date) {
			frm.doc.posting_date = frappe.datetime.nowdate();
		}
	},
  department_filters: function (frm) {
		frm.set_query("department", function () {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

  refresh: function (frm) {
    if (frm.doc.docstatus === 0 && !frm.is_new()) {
      frm.page.clear_primary_action();
      frm.add_custom_button(__("Get Employees"),
        function() {
          frm.events.get_employee_details(frm);
        }
      ).toggleClass("btn-primary", !(frm.doc.employees || []).length);
    }

    if (
      (frm.doc.employees || []).length
      && !frappe.model.has_workflow(frm.doctype)
      //&& !cint(frm.doc.salary_slips_created)
      && (frm.doc.docstatus != 2)
    ) {
      if (frm.doc.docstatus == 0) {
        frm.page.clear_primary_action();
        frm.page.set_primary_action(__("Create Salary Slips"), () => {
          frm.save("Submit").then(() => {
            frm.page.clear_primary_action();
            frm.refresh();
            frm.events.refresh(frm);
          });
        });
      } else if (frm.doc.docstatus == 1 && frm.doc.status == "Failed") {
        frm.add_custom_button(__("Create Salary Slip"), function () {
          frm.call("create_salary_slips", {}, () => {
            frm.reload_doc();
          });
        }).addClass("btn-primary");
      }
    }

    if (frm.doc.docstatus == 1 && frm.doc.status == "Submitted") {
      if (frm.custom_buttons) frm.clear_custom_buttons();
      frm.events.add_context_buttons(frm);
    }

    if (frm.doc.status == "Failed" && frm.doc.error_message) {
      const issue = `<a id="jump_to_error" style="text-decoration: underline;">issue</a>`;
      let process = (cint(frm.doc.salary_slips_created)) ? "submission" : "creation";

      frm.dashboard.set_headline(
        __("Salary Slip {0} failed. You can resolve the {1} and retry {0}.", [process, issue])
      );

      $("#jump_to_error").on("click", (e) => {
        e.preventDefault();
        frappe.utils.scroll_to(
          frm.get_field("error_message").$wrapper,
          true,
          30
        );
      });
    }

    frappe.realtime.on("completed_salary_slip_creation", function() {
      frm.reload_doc();
    });

    frappe.realtime.on("completed_salary_slip_submission", function() {
      frm.reload_doc();
    });
  },

  get_employee_details: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_employee_details',
		}).then(r => {
			if (r.docs && r.docs[0].employees) {
				frm.employees = r.docs[0].employees;
				frm.dirty();
				frm.save();
				frm.refresh();
				if (r.docs[0].validate_attendance) {
					render_employee_attendance(frm, r.message);
				}
				frm.scroll_to_field("employees");
			}
		});
	},




});
