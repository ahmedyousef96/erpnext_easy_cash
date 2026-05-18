import frappe
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe import _


class EasyCashEntry(AccountsController):
	def get_voucher_subtype(self):
		return self.entry_type

	def before_validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if not self.company:
			self.company = frappe.defaults.get_user_default("Company")
		if not self.conversion_rate:
			self.conversion_rate = 1.0
		self.calculate_total()

	def validate(self):
		self.validate_cash_account()
		self.validate_category_lines()
		self.validate_treasury()
		self.validate_currency_is_company_currency()
		self.validate_category_currencies()

	def validate_cash_account(self):
		if not self.cash_account:
			frappe.throw(
				_("Cash account not found. Please check treasury setup."),
				title=_("Missing Cash Account"),
			)

	def validate_category_lines(self):
		if not self.category_lines:
			frappe.throw(
				_("At least one category line is required"),
				title=_("Missing Lines"),
			)
		all_categories = list(set(row.category for row in self.category_lines if row.category))
		if all_categories:
			category_data = frappe.db.get_values(
				"Easy Cash Category",
				filters={"name": ["in", all_categories]},
				fieldname=["name", "type", "disabled"],
				as_dict=True,
			)
			category_map = {c["name"]: c for c in category_data}
		else:
			category_map = {}
		for row in self.category_lines:
			if (row.amount or 0) <= 0:
				frappe.throw(
					_("Amount must be greater than zero in row {0}").format(row.idx),
					title=_("Invalid Amount"),
				)
			if row.category:
				cat = category_map.get(row.category)
				if not cat:
					continue
				if cat.get("disabled"):
					frappe.throw(
						_("Category {0} is disabled").format(row.category),
						title=_("Disabled Category"),
					)
				if cat.get("type") != self.entry_type:
					frappe.throw(
						_("Category {0} is of type {1}, but entry type is {2}").format(
							row.category, cat.get("type"), self.entry_type
						),
						title=_("Category Type Mismatch"),
					)

	def validate_treasury(self):
		if not self.treasury:
			return
		treasury_data = frappe.db.get_value("Treasury", self.treasury, ["company", "disabled"], as_dict=True)
		if not treasury_data:
			return
		if treasury_data.disabled:
			frappe.throw(
				_("Treasury {0} is disabled").format(self.treasury),
				title=_("Disabled Treasury"),
			)
		if treasury_data.company != self.company:
			frappe.throw(
				_("Treasury does not belong to company {0}").format(self.company),
				title=_("Invalid Treasury"),
			)

	def validate_currency_is_company_currency(self):
		if self.currency and self.company:
			company_currency = frappe.db.get_value("Company", self.company, "default_currency")
			if company_currency and self.currency != company_currency:
				frappe.throw(
					_(
						"Multi-currency entries are not supported yet.<br>"
						"Entry currency ({0}) must match company currency ({1}).<br><hr>"
						"<b>Contact for multi-currency support:</b><br>"
						'<span class="fa fa-whatsapp" style="color:#25D366"></span> '
						'<a href="https://api.whatsapp.com/send/?phone=201028171836&text=Hello%2C+I%27m+contacting+you+for+App+Easy+Cash+Support&type=phone_number&app_absent=0" target="_blank">'
						"WhatsApp/Call: +201028171836</a><br>"
						'<span class="fa fa-envelope" style="color:#ea4335"></span> '
						'<a href="mailto:Ay716881@gmail.com?subject=Easy Cash App - Multi-currency Support">'
						"Email: Ay716881@gmail.com</a>"
					).format(self.currency, company_currency),
					title=_("Currency Not Supported"),
				)

	def validate_category_currencies(self):
		if not self.currency:
			return
		accounts = list(set(row.account for row in self.category_lines if row.account))
		if not accounts:
			return
		account_currencies = frappe.db.get_values(
			"Account",
			filters={"name": ["in", accounts]},
			fieldname=["name", "account_currency"],
			as_dict=True,
		)
		currency_map = {a["name"]: a["account_currency"] for a in account_currencies}
		for row in self.category_lines:
			if row.account:
				account_currency = currency_map.get(row.account)
				if account_currency and account_currency != self.currency:
					frappe.throw(
						_("Row {0}: Account {1} currency ({2}) does not match entry currency ({3})").format(
							row.idx, row.account, account_currency, self.currency
						),
						title=_("Currency Mismatch"),
					)

	def before_submit(self):
		self.calculate_total()
		self.set_remarks()

	def set_remarks(self):
		if not self.remarks:
			self.remarks = _("{0} - {1} via Easy Cash Entry {2}").format(
				self.entry_type,
				frappe.format_value(self.total_amount, currency=self.currency),
				self.name,
			)

	def calculate_total(self):
		total = sum((row.amount or 0) for row in self.category_lines)
		self.total_amount = total

	def on_submit(self):
		gl_entries = self.get_gl_entries()
		if gl_entries:
			make_gl_entries(gl_entries)

	def on_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry"]
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	def get_gl_entries(self):
		gl_entries = []

		for row in self.category_lines:
			remarks_parts = [row.description, self.remarks]
			remarks = "\n".join([r for r in remarks_parts if r])

			if self.entry_type == "Cash Out":
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": row.account,
							"debit": row.amount,
							"credit": 0,
							"against": self.cash_account,
							"cost_center": row.cost_center,
							"remarks": remarks,
						},
						item=row,
					)
				)
			else:
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": row.account,
							"debit": 0,
							"credit": row.amount,
							"against": self.cash_account,
							"cost_center": row.cost_center,
							"remarks": remarks,
						},
						item=row,
					)
				)

		against_accounts = ", ".join(set(row.account for row in self.category_lines if row.account))

		if self.entry_type == "Cash Out":
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.cash_account,
						"debit": 0,
						"credit": self.total_amount,
						"against": against_accounts,
					}
				)
			)
		else:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.cash_account,
						"debit": self.total_amount,
						"credit": 0,
						"against": against_accounts,
					}
				)
			)

		return gl_entries
