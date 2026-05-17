import frappe
from frappe import _
from frappe.model.document import Document


class Treasury(Document):
	def validate(self):
		self.validate_account()
		self.validate_account_company()

	def on_trash(self):
		if frappe.db.exists("Easy Cash Entry", {"treasury": self.name, "docstatus": 1}):
			frappe.throw(
				_("Cannot delete Treasury with submitted Easy Cash Entries"),
				title=_("Cannot Delete"),
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
