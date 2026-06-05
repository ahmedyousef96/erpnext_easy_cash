import frappe
from frappe import _
from frappe.model.document import Document

from easy_cash.api.plan import validate_treasury_limit


class Treasury(Document):
	def validate(self):
		if self.is_new():
			validate_treasury_limit(self.company)
		self.validate_account()
		self.validate_account_company()
		self.validate_account_change()

	def on_trash(self):
		if self.has_active_entries():
			frappe.throw(
				_("Cannot delete Treasury with active Easy Cash Entries"),
				title=_("Cannot Delete"),
			)

	def has_active_entries(self):
		return frappe.db.exists("Easy Cash Entry", {"treasury": self.name, "docstatus": ["in", [0, 1]]})

	def validate_account_change(self):
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before and before.account != self.account:
			if self.has_active_entries():
				frappe.throw(
					_(
						"Cannot change Account because this Treasury is used in Easy Cash Entries. "
						"Disable it and create a new Treasury instead."
					),
					title=_("Treasury In Use"),
				)

	def validate_account(self):
		account_type = frappe.db.get_value("Account", self.account, "account_type")
		if account_type not in ("Cash", "Bank"):
			frappe.throw(
				_("Account must be of type Cash or Bank"),
				title=_("Invalid Account"),
			)

	def validate_account_company(self):
		account_company = frappe.db.get_value("Account", self.account, "company")
		if account_company != self.company:
			frappe.throw(
				_("Account does not belong to company {0}").format(self.company),
				title=_("Invalid Account"),
			)
