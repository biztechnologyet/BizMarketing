import frappe

def execute(filters=None):
	columns = [
		{"label": "Campaign", "fieldname": "campaign", "fieldtype": "Link", "options": "Marketing Campaign", "width": 200},
		{"label": "Total Budget", "fieldname": "budget", "fieldtype": "Currency", "width": 120},
		{"label": "Actual Spend", "fieldname": "actual_spend", "fieldtype": "Currency", "width": 120},
		{"label": "Variance", "fieldname": "variance", "fieldtype": "Currency", "width": 120}
	]
	data = frappe.db.sql("""
		SELECT
			name as campaign,
			budget,
			actual_spend,
			(budget - actual_spend) as variance
		FROM
			`tabMarketing Campaign`
		WHERE
			docstatus < 2
	""", as_dict=1)
	return columns, data
