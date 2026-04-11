frappe.views.calendar["Publishing Queue"] = {
	field_map: {
		"start": "scheduled_time",
		"end": "scheduled_time",
		"id": "name",
		"title": "social_media_post",
		"allDay": "allDay"
	},
	gantt: false,
	get_events_method: "frappe.desk.calendar.get_events",
};
