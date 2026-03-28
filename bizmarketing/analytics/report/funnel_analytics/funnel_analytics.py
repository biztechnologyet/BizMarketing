import frappe

def execute(filters=None):
	columns = [
		{"label": "Funnel", "fieldname": "funnel", "fieldtype": "Link", "options": "Marketing Funnel", "width": 200},
		{"label": "Stage", "fieldname": "stage_name", "fieldtype": "Data", "width": 150},
		{"label": "Lead Count", "fieldname": "lead_count", "fieldtype": "Int", "width": 100},
		{"label": "Conversion Rate", "fieldname": "conversion_rate", "fieldtype": "Percent", "width": 120}
	]
	data = []
	# Placeholder logic
	return columns, data
