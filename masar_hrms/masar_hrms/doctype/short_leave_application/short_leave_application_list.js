
frappe.listview_settings["Short Leave Application"] = {
	add_fields: ["leave_type", "employee", "employee_name", "total_leave_hours", "from_time", "to_time"],
	has_indicator_for_draft: 1,
	get_indicator: function (doc) {
		let status_color = {
			"Approved": "green",
			"Rejected": "red",
			"Open": "orange",
			"Cancelled": "red",
			"Submitted": "blue"
		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	}
};
