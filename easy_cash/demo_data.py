import frappe
from frappe import _
from frappe.utils import getdate, now


def create_demo_data(company=None):
	if not company:
		company = frappe.db.get_value("Company", {}, "name")

	if not company:
		frappe.throw(_("No company found"))

	cost_center = frappe.db.get_value("Company", company, "cost_center")
	if not cost_center:
		frappe.throw(_("No default cost center found for {0}").format(company))

	cash_account = _get_cash_account(company)
	expense_account = _get_expense_account(company)
	income_account = _get_income_account(company)

	treasury = _create_treasury(company, cash_account)
	categories = _create_categories(company, expense_account, income_account)
	entries = _create_entries(company, treasury, categories, cost_center)

	frappe.db.commit()

	return {
		"treasury": treasury,
		"categories": len(categories),
		"entries": len(entries),
	}


def _get_cash_account(company):
	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "account_type": "Cash", "is_group": 0},
		pluck="name",
	)
	if not accounts:
		frappe.throw(_("No Cash account found for {0}").format(company))
	return accounts[0]


def _get_expense_account(company):
	for name in ["Administrative Expenses", "Indirect Expenses", "Operating Expenses"]:
		accounts = frappe.get_all(
			"Account",
			filters={"company": company, "account_name": name, "is_group": 0},
			pluck="name",
		)
		if accounts:
			return accounts[0]

	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "root_type": "Expense", "is_group": 0},
		pluck="name",
	)
	if not accounts:
		frappe.throw(_("No Expense account found for {0}").format(company))
	return accounts[0]


def _get_income_account(company):
	for name in ["Sales", "Service", "Direct Income", "Operating Revenue"]:
		accounts = frappe.get_all(
			"Account",
			filters={"company": company, "account_name": name, "is_group": 0},
			pluck="name",
		)
		if accounts:
			return accounts[0]

	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "root_type": "Income", "is_group": 0},
		pluck="name",
	)
	if not accounts:
		frappe.throw(_("No Income account found for {0}").format(company))
	return accounts[0]


def _create_treasury(company, cash_account):
	if frappe.db.exists("Treasury", "Main Cash Box"):
		return "Main Cash Box"

	doc = frappe.get_doc(
		{
			"doctype": "Treasury",
			"treasury_name": "Main Cash Box",
			"company": company,
			"account": cash_account,
		}
	)
	doc.insert()
	return doc.name


def _create_categories(company, expense_account, income_account):
	categories = {
		"Administrative Expenses": {"type": "Cash Out", "account": expense_account},
		"Transportation": {"type": "Cash Out", "account": expense_account},
		"Office Supplies": {"type": "Cash Out", "account": expense_account},
		"Utilities": {"type": "Cash Out", "account": expense_account},
		"Sales Revenue": {"type": "Cash In", "account": income_account},
		"Service Income": {"type": "Cash In", "account": income_account},
	}

	created = []
	for name, opts in categories.items():
		if frappe.db.exists("Easy Cash Category", name):
			created.append(name)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Easy Cash Category",
				"category_name": name,
				"company": company,
				"type": opts["type"],
				"account": opts["account"],
			}
		)
		doc.insert()
		created.append(name)

	return created


def _create_entries(company, treasury, categories, cost_center):
	entries_data = [
		{
			"entry_type": "Cash Out",
			"category": "Administrative Expenses",
			"amount": 500,
			"description": "Monthly office rent payment",
			"posting_date": "2026-05-10 09:30:00",
			"reference_no": "REF-001",
			"remarks": "Monthly rent for May 2026",
		},
		{
			"entry_type": "Cash Out",
			"category": "Transportation",
			"amount": 150,
			"description": "Delivery charges for client orders",
			"posting_date": "2026-05-11 11:00:00",
			"reference_no": "REF-002",
			"remarks": "",
		},
		{
			"entry_type": "Cash Out",
			"category": "Office Supplies",
			"amount": 75,
			"description": "Printer paper and ink cartridges",
			"posting_date": "2026-05-12 14:15:00",
			"reference_no": "",
			"remarks": "Emergency purchase",
		},
		{
			"entry_type": "Cash Out",
			"category": "Utilities",
			"amount": 200,
			"description": "Electricity bill - March",
			"posting_date": "2026-05-13 10:00:00",
			"reference_no": "UTIL-2026-03",
			"remarks": "",
		},
		{
			"entry_type": "Cash In",
			"category": "Sales Revenue",
			"amount": 3000,
			"description": "Cash sale - Walk-in customer",
			"posting_date": "2026-05-14 16:45:00",
			"reference_no": "SR-001",
			"remarks": "Walk-in purchase",
		},
		{
			"entry_type": "Cash In",
			"category": "Service Income",
			"amount": 1500,
			"description": "Consulting service payment received",
			"posting_date": "2026-05-15 09:00:00",
			"reference_no": "SVC-001",
			"remarks": "IT consulting for ABC Corp",
		},
		{
			"entry_type": "Cash Out",
			"category": "Administrative Expenses",
			"amount": 300,
			"description": "Staff lunch and refreshments",
			"posting_date": "2026-05-16 13:00:00",
			"reference_no": "",
			"remarks": "Team meeting lunch",
		},
		{
			"entry_type": "Cash In",
			"category": "Sales Revenue",
			"amount": 2200,
			"description": "Product sales batch order",
			"posting_date": "2026-05-17 11:30:00",
			"reference_no": "SR-002",
			"remarks": "Bulk order from XYZ Ltd",
		},
	]

	created = []
	for entry_data in entries_data:
		if not entry_data["category"] in categories:
			continue

		category_type = frappe.db.get_value("Easy Cash Category", entry_data["category"], "type")

		doc = frappe.get_doc(
			{
				"doctype": "Easy Cash Entry",
				"company": company,
				"entry_type": entry_data["entry_type"],
				"treasury": treasury,
				"posting_date": entry_data["posting_date"],
				"reference_no": entry_data.get("reference_no", ""),
				"remarks": entry_data.get("remarks", ""),
				"category_lines": [
					{
						"category": entry_data["category"],
						"description": entry_data["description"],
						"amount": entry_data["amount"],
						"cost_center": cost_center,
					}
				],
			}
		)
		doc.insert()
		doc.submit()
		created.append(doc.name)

	return created
