frappe.listview_settings['Attendance Shortage'] = {
    onload: function(list) {
        list.page.add_inner_button(
            __('Get Attendance Details'),
            function() {
                frappe.call({
                    method: 'masar_hrms.masar_hrms.doctype.attendance_shortage.attendance_shortage.get_employee_attendance',
                    callback: function(ret) {},
                });
            },
            null,
            'primary'
        );
    }
};
