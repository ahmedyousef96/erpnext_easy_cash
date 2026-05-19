import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	filters = frappe._dict(filters)
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)

	return columns, data, None, chart


def validate_filters(filters):
	if not filters.company:
		frappe.throw(_("Company is required"))

	if filters.from_date and filters.to_date:
		if getdate(filters.from_date) > getdate(filters.to_date):
			frappe.throw(_("From Date must be before To Date"))


def get_columns():
	return [
		{
			"fieldname": "category",
			"label": _("Category"),
			"fieldtype": "Link",
			"options": "Easy Cash Category",
			"width": 200,
		},
		{
			"fieldname": "type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 200,
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Data",
			"hidden": 1,
		},
	]


def get_data(filters):
	conditions = "ece.docstatus = 1 AND ece.company = %(company)s"
	filter_values = {"company": filters.company}

	if filters.from_date:
		conditions += " AND DATE(ece.posting_date) >= %(from_date)s"
		filter_values["from_date"] = filters.from_date

	if filters.to_date:
		conditions += " AND DATE(ece.posting_date) <= %(to_date)s"
		filter_values["to_date"] = filters.to_date

	if filters.entry_type:
		conditions += " AND ece.entry_type = %(entry_type)s"
		filter_values["entry_type"] = filters.entry_type

	if filters.treasury:
		conditions += " AND ece.treasury = %(treasury)s"
		filter_values["treasury"] = filters.treasury

	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")

	results = frappe.db.sql(
		"""
		SELECT
			eced.category,
			ecc.type,
			ecc.account,
			SUM(eced.amount) as total_amount,
			ece.currency
		FROM `tabEasy Cash Entry Detail` eced
		JOIN `tabEasy Cash Entry` ece ON ece.name = eced.parent
		JOIN `tabEasy Cash Category` ecc ON ecc.name = eced.category
		WHERE """
		+ conditions
		+ """
		GROUP BY eced.category
		ORDER BY total_amount DESC
	""",
		filter_values,
		as_dict=1,
	)

	data = []
	for row in results:
		data.append(
			{
				"category": row.category,
				"type": row.type,
				"account": row.account,
				"total_amount": row.total_amount,
				"currency": row.currency or company_currency,
			}
		)

	return data


def get_chart_data(data):
	if not data:
		return None

	labels = []
	values = []
	colors = []

	for row in data:
		labels.append(row.get("category", ""))
		values.append(flt(row.get("total_amount", 0)))
		if row.get("type") == "Cash In":
			colors.append("#218c2a")
		else:
			colors.append("#c42828")

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("Amount"),
					"values": values,
				}
			],
		},
		"type": "bar",
		"colors": colors,
	}
