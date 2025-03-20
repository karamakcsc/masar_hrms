frappe.ui.form.on('Goal', {
    refresh: function(frm) {
        removeUserEmp(frm);
    },
    setup: function(frm) {
        removeUserEmp(frm);
    },
  });

  function removeUserEmp(frm) {
    frappe.call({
        method: "masar_hrms.custom.goal.goal.get_emp",
        args: {
            user: frappe.session.user
        },
        callback: function(r) {
            if (r.message) {
                var emp_name = r.message;

                frm.fields_dict['employee'].get_query = function(doc) {
                    return {
                        filters: {
                            "name": ["not in", [emp_name]]
                        }
                    };
                };
            }
        }
    });
  }

//   function removeSubmit(frm) {
//     frappe.call({
//         method: "masar_hrms.custom.goal.goal.get_manager",
//         args: {
//             emp: frm.doc.employee
//         },
//         callback: function(r) {
//             if (r.message) {
//                 var manager_user = r.message;
//                 // if (frappe.session.user !== manager_user || !frappe.user.has_role('HR User') || !frappe.user.has_role('HR Manager')) {
//                     $('.primary-action').prop('disabled', true);
//                 // }
//             }
//         }
//     }) 
//   }