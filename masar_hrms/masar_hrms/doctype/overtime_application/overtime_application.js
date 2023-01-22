// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Overtime Application', {
// 	// refresh: function(frm) {
//
// 	// }
// });


// ///// Add MultiSelectDialog /////Siam//////Satrt Code//
frappe.ui.form.on("Overtime Application", {
  refresh: function(frm){
  frm.fields_dict["overtime_employees"].grid.add_custom_button(__('Get Employee'),
   function() {
     let query_args = {
     query: "masar_hr.masar_hr.doctype.overtime_application.overtime_application.get_employee_qry",
     filters: {'department': frm.doc.department}
 }
    var f = new frappe.ui.form.MultiSelectDialog({
      doctype: "Employee",
      target: me.frm,
      setters: {
        employee_name: '',
				company: '',
				department: '',
      },
      date_field: "overtime_employees",
      primary_action_label: "Get Employee",
      action(selected_employees) {
        frappe.call({
          method: "masar_hr.masar_hr.doctype.overtime_application.overtime_application.insert_selected_employee",
          args: {
            selected_employees: selected_employees
          },
          callback: function(r) {
            $.each(r.message, function(i, d) {
              var row = frappe.model.add_child(frm.doc, "Overtime Employee", "overtime_employees");
              row.employee = d.name;
              // row.item_code = frm.doc.item_code;
              refresh_field("overtime_employees");
            });
          }
        });
        f.dialog.hide();
      }
    			});
        f.dialog.get_secondary_btn().addClass('hide').off('click');

      }
    )
  	frm.fields_dict["overtime_employees"].grid.grid_buttons.find('.btn-custom').removeClass('btn-default').addClass('btn-primary');
  }

  });

// ///// Add MultiSelectDialog /////Siam//////END Code//

////// Fetching Employee with Filter ///// Start ///Siam
frappe.ui.form.on("Overtime Application", "refresh", function(frm) {
    frm.fields_dict['overtime_employees'].grid.get_field('employee').get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        //console.log(child);
        return {
            filters: {
                "is_overtime_applicable": 1
            }
        };
    };
});
////// Fetching Employee with Filter ///// END ///Siam

// Start Calculate button
// frappe.ui.form.on("Overtime Application", "refresh", function(frm) {
//     frm.add_custom_button(__("Calculate"), function() {
//       frappe.call({
//           method: 'masar_hr.masar_hr.doctype.overtime_application.overtime_application.demo_salary_slip',
//           args: {
//             employee: "M1169",
//             posting_date: frm.doc.posting_date,
//           },
//           callback: function(ret) {
//             frappe.msgprint("Done")
//           },
//       });
//  }
//  ,);
//
// });
// END Calculate button
