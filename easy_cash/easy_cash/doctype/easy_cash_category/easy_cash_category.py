import frappe
from frappe import _
from frappe.model.document import Document


class EasyCashCategory(Document):
	def validate(self):
		self.validate_field_changes()
		self.validate_account_is_leaf()
		self.validate_account_company()
		self.validate_account_root_type()

	def validate_field_changes(self):
		if self.is_new():
			return

		before = self.get_doc_before_save()
		if not before:
			return
		if before.type != self.type or before.account != self.account:
			active_entries = frappe.db.sql(
				"""
				SELECT ece.name
				FROM `tabEasy Cash Entry Detail` eced
				JOIN `tabEasy Cash Entry` ece ON ece.name = eced.parent
				WHERE eced.category = %s AND ece.docstatus IN (0, 1)
				LIMIT 1
			""",
				self.name,
			)
			if active_entries:
				frappe.throw(
					_(
						"Cannot change Type or Account because this category is used in Easy Cash Entries. Disable it and create a new category instead."
					),
					title=_("Category In Use"),
				)

	def validate_account_is_leaf(self):
		if frappe.db.get_value("Account", self.account, "is_group"):
			frappe.throw(
				_("Account must be a leaf account, not a group"),
				title=_("Group Account"),
			)

	def validate_account_company(self):
		account_company = frappe.db.get_value("Account", self.account, "company")
		if account_company != self.company:
			frappe.throw(
				_("Account does not belong to company {0}").format(self.company),
				title=_("Invalid Account"),
			)

	def validate_account_root_type(self):
		root_type = frappe.db.get_value("Account", self.account, "root_type")
		if self.type == "Cash In" and root_type != "Income":
			frappe.throw(
				_("Cash In categories must use an Income account"),
				title=_("Invalid Account Type"),
			)
		if self.type == "Cash Out" and root_type not in ("Expense", "Asset"):
			frappe.throw(
				_("Cash Out categories must use an Expense or Asset account"),
				title=_("Invalid Account Type"),
			)
