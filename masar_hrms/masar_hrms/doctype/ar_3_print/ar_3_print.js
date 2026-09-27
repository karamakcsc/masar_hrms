// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("AR 3 Print", {
	setup: function(frm) {
		frm.set_query("print_format", function() {
			return { filters: { doc_type: "Salary Slip" } };
		});
	},
	onload: function(frm) {
		if (frm.is_new() && !frm.doc.year) {
			frm.set_value("year", new Date().getFullYear());
		}
	},
	refresh: function(frm) {
		frappe.realtime.off("ar3_pdf_complete");
		frappe.realtime.on("ar3_pdf_complete", function(data) {
			if (data.docname !== frm.doc.name) return;
			frm.reload_doc();
			if (data.status === "Completed") {
				frappe.show_alert({ message: __("PDF generated successfully."), indicator: "green" });
			} else {
				frappe.show_alert({ message: __("PDF generation failed. Check the Error Log."), indicator: "red" });
			}
		});
	},
	get_salary_slips: function(frm) {
        addChild(frm);
	},
	generate_pdf: function(frm) {
		if (!frm.doc.print_format) {
			frappe.msgprint(__("Please select a Print Format first."));
			return;
		}
		if (!(frm.doc.ss_table || []).length) {
			frappe.msgprint(__("Please fetch the Salary Slips first."));
			return;
		}
		if (frm.is_dirty()) {
			frappe.msgprint(__("Please save the document before generating the PDF."));
			return;
		}
		frappe.call({
			doc: frm.doc,
			method: "generate_pdf",
			callback: function(r) {
				if (!r.exc) {
					frappe.show_alert({ message: __("PDF generation started in the background."), indicator: "blue" });
					frm.reload_doc();
				}
			}
		});
	},
});

function addChild(frm) {
    if (frm.doc.month && frm.doc.year) {
        frappe.call({
            doc: frm.doc,
            method: "get_ss",
            callback: function(r) {
                console.log("Success");
                if (r.message) {
                    frm.clear_table('ss_table');
                    r.message.forEach(emp => {
                        var row = frm.add_child("ss_table");
                        row.salary_slip = emp.name;
                        row.employee = emp.employee;
                        row.employee_name = emp.employee_name;

                    });
                    frm.refresh_field('ss_table');
                }
            }
        })
    }
}
