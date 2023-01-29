frappe.views.calendar["Short Leave Application"] = {
	field_map: {
		"start": "from_time",
		"end": "to_time",
		"id": "name",
		"title": "title",
		"docstatus": 1,
		"color": "color",
		"allDay": "all_day"
	},
	options: {
		header: {
			left: 'prev,next today',
			center: 'title',
			right: 'month'
		}
	},
	get_events_method: "hrms.hr.doctype.leave_application.leave_application.get_events"
}
