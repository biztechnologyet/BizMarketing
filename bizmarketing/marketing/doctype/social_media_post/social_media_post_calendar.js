frappe.views.calendar["Social Media Post"] = {
	field_map: {
		"start": "scheduled_time",
		"end": "scheduled_time",
		"id": "name",
		"title": "title",
		"allDay": "allDay"
	},
	gantt: false,
	get_events_method: "frappe.desk.calendar.get_events",
};
