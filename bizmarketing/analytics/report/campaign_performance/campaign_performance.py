import frappe

def execute(filters=None):
	columns, data = [], []
	columns = [
		{"label": "Campaign", "fieldname": "campaign", "fieldtype": "Link", "options": "Marketing Campaign", "width": 200},
		{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Budget", "fieldname": "budget", "fieldtype": "Currency", "width": 120},
		{"label": "Actual Spend", "fieldname": "actual_spend", "fieldtype": "Currency", "width": 120},
		{"label": "ROI", "fieldname": "roi", "fieldtype": "Percent", "width": 100}
	]

	data = frappe.db.sql("""
		SELECT
			name as campaign,
			type,
			status,
			budget,
			actual_spend,
			CASE WHEN actual_spend > 0 THEN ((budget - actual_spend) / actual_spend) * 100 ELSE 0 END as roi
		FROM
			`tabMarketing Campaign`
		WHERE
			docstatus < 2
	""", as_dict=1)

	return columns, data
