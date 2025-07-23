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