import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	filters = frappe._dict(filters)
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def validate_filters(filters):
	if not filters.company:
		frappe.throw(_("Company is required"))

	if filters.from_date and filters.to_date:
		if getdate(filters.from_date) > getdate(filters.to_date):
			frappe.throw(_("From Date must be before To Date"))


def get_columns():
	return [
		{
			"fieldname": "voucher_no",
			"label": _("Voucher No"),
			"fieldtype": "Link",
			"options": "Easy Cash Entry",
			"width": 140,
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Datetime",
			"width": 160,
		},
		{
			"fieldname": "entry_type",
			"label": _("Entry Type"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"fieldname": "treasury",
			"label": _("Treasury"),
			"fieldtype": "Link",
			"options": "Treasury",
			"width": 150,
		},
		{
			"fieldname": "reference_no",
			"label": _("Reference No"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "category",
			"label": _("Category"),
			"fieldtype": "Link",
			"options": "Easy Cash Category",
			"width": 150,
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "name",
			"label": _("Name"),
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "parent_entry",
			"label": _("Parent Entry"),
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "indent",
			"label": _("Indent"),
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Data",
			"hidden": 1,
		},
	]


def get_data(filters):
	parents = get_parent_entries(filters)

	if not parents:
		return []

	parent_names = [p.name for p in parents]
	children = get_child_entries(parent_names, filters)

	if filters.category:
		parent_names_with_match = list(set(c.parent_entry for c in children))
		parents = [p for p in parents if p.name in parent_names_with_match]

	if not parents:
		return []

	children_by_parent = {}
	for child in children:
		children_by_parent.setdefault(child.parent_entry, []).append(child)

	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")

	data = []
	for parent in parents:
		parent_children = children_by_parent.get(parent.name, [])
		if not parent_children:
			continue

		currency = parent.currency or company_currency

		parent_row = {
			"name": parent.name,
			"voucher_no": parent.name,
			"posting_date": parent.posting_date,
			"entry_type": parent.entry_type,
			"treasury": parent.treasury,
			"reference_no": parent.reference_no,
			"total_amount": parent.total_amount,
			"remarks": parent.remarks,
			"currency": currency,
			"parent_entry": "",
			"indent": 0,
		}
		data.append(parent_row)

		for child in parent_children:
			child_row = {
				"name": child.name,
				"parent_entry": parent.name,
				"category": child.category,
				"description": child.description,
				"amount": child.amount,
				"currency": currency,
				"indent": 1,
			}
			data.append(child_row)

	return data


def get_parent_entries(filters):
	conditions = "docstatus = 1 AND company = %(company)s"
	filter_values = {"company": filters.company}

	if filters.from_date:
		conditions += " AND DATE(posting_date) >= %(from_date)s"
		filter_values["from_date"] = filters.from_date

	if filters.to_date:
		conditions += " AND DATE(posting_date) <= %(to_date)s"
		filter_values["to_date"] = filters.to_date

	if filters.entry_type:
		conditions += " AND entry_type = %(entry_type)s"
		filter_values["entry_type"] = filters.entry_type

	if filters.treasury:
		conditions += " AND treasury = %(treasury)s"
		filter_values["treasury"] = filters.treasury

	return frappe.db.sql(
		"""
		SELECT name, posting_date, entry_type, treasury, reference_no,
			total_amount, remarks, currency
		FROM `tabEasy Cash Entry`
		WHERE """
		+ conditions
		+ """
		ORDER BY posting_date DESC, name DESC
	""",
		filter_values,
		as_dict=1,
	)


def get_child_entries(parent_names, filters):
	if not parent_names:
		return []

	conditions = "parent IN %(parent_names)s"
	filter_values = {"parent_names": parent_names}

	if filters.category:
		conditions += " AND category = %(category)s"
		filter_values["category"] = filters.category

	return frappe.db.sql(
		"""
		SELECT name, parent as parent_entry, category, description, amount
		FROM `tabEasy Cash Entry Detail`
		WHERE """
		+ conditions
		+ """
		ORDER BY idx
	""",
		filter_values,
		as_dict=1,
	)
