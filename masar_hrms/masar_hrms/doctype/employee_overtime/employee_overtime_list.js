frappe.listview_settings['Employee Overtime'] = {
    onload: function(list) {
        list.page.add_inner_button(
            __('Get Attendance Details'),
            function() {
                var today = frappe.datetime.nowdate();
                var firstDayOfMonth = frappe.datetime.month_start(today);
                var lastDayOfMonth = frappe.datetime.month_end(today);
                frappe.prompt(
                    [
                        {
                            fieldname: 'date_from',
                            fieldtype: 'Date',
                            label: __('From Date'),
                            'default': firstDayOfMonth,
                            reqd: 1,
                            bold: 1
                        },
                        {
                            fieldname: 'date_to',
                            fieldtype: 'Date',
                            label: __('To Date'),
                            'default': lastDayOfMonth,
                            reqd: 1,
                            bold: 1
                        },
                        {
                            fieldname: 'department',
                            fieldtype: 'Link',
                            label: __('Department'),
                            options: 'Department',
                            reqd: 0,
                            bold: 1, 
                        }
                    ],
                    function(values) {
                        frappe.call({
                            method: 'masar_hrms.masar_hrms.doctype.employee_overtime.employee_overtime.get_employee_attendance',
                            args: {
                                date_from: values.date_from,
                                date_to: values.date_to,
                                department:values.department,
                            },
                            callback: function(ret) {},
                        });
                        frappe.show_alert({
                            message: __('Sync has started in the background.'),
                            indicator: 'green',
                        });
                        frappe.socketio.init();
                        frappe.realtime.on('get_employee_attendance', function() {
                            list.refresh();
                        });
                    },
                    __('Sync Date Range'),
                    __('Get')
                );
            },
            null,
            'primary'
        );
    }
};