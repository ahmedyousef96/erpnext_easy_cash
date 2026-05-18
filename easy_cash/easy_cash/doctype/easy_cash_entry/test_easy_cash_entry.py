import frappe
from frappe import qb
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, nowdate


class TestEasyCashEntry(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._setup_test_data()

	@classmethod
	def _setup_test_data(cls):
		cls.company = "_Test Easy Cash Co"
		cls.abbr = "_TEC"
		if not frappe.db.exists("Company", cls.company):
			company = frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": cls.company,
					"abbr": cls.abbr,
					"country": "Egypt",
					"default_currency": "EGP",
					"create_chart_of_accounts_based_on": "Standard Template",
					"chart_of_accounts": "Standard",
				}
			)
			company.insert()
		else:
			company = frappe.get_doc("Company", cls.company)

		cls.cost_center = company.cost_center
		cls.currency = "EGP"

		cls.cash_account = cls._make_account(
			account_name="Test Cash",
			account_type="Cash",
			parent_account="Cash In Hand - " + cls.abbr,
		)
		cls.income_account = cls._make_account(
			account_name="Test Sales Revenue",
			parent_account="Direct Income - " + cls.abbr,
		)
		cls.expense_account = cls._make_account(
			account_name="Test Admin Expenses",
			parent_account="Indirect Expenses - " + cls.abbr,
		)

		if not frappe.db.exists("Treasury", "Test Treasury"):
			frappe.get_doc(
				{
					"doctype": "Treasury",
					"treasury_name": "Test Treasury",
					"company": cls.company,
					"account": cls.cash_account,
				}
			).insert()

		if not frappe.db.exists("Easy Cash Category", "Test Sales Revenue"):
			frappe.get_doc(
				{
					"doctype": "Easy Cash Category",
					"category_name": "Test Sales Revenue",
					"type": "Cash In",
					"company": cls.company,
					"account": cls.income_account,
				}
			).insert()

		if not frappe.db.exists("Easy Cash Category", "Test Admin Expenses"):
			frappe.get_doc(
				{
					"doctype": "Easy Cash Category",
					"category_name": "Test Admin Expenses",
					"type": "Cash Out",
					"company": cls.company,
					"account": cls.expense_account,
				}
			).insert()

		frappe.db.commit()

	@classmethod
	def _make_account(cls, account_name, parent_account, account_type=None):
		existing = frappe.db.get_value(
			"Account",
			filters={"account_name": account_name, "company": cls.company},
		)
		if existing:
			return existing
		acc = frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": account_name,
				"parent_account": parent_account,
				"company": cls.company,
				"account_type": account_type,
			}
		)
		acc.insert()
		return acc.name

	def tearDown(self):
		frappe.db.rollback()

	def _create_entry(self, entry_type="Cash In", lines=None, submit=False, **kwargs):
		if lines is None:
			cat = "Test Sales Revenue" if entry_type == "Cash In" else "Test Admin Expenses"
			lines = [{"category": cat, "amount": 100}]

		doc = frappe.new_doc("Easy Cash Entry")
		doc.company = kwargs.pop("company", self.company)
		doc.entry_type = entry_type
		doc.posting_date = kwargs.pop("posting_date", nowdate())
		doc.treasury = kwargs.pop("treasury", "Test Treasury")
		for key, value in kwargs.items():
			setattr(doc, key, value)
		for line in lines:
			if "cost_center" not in line:
				line["cost_center"] = self.cost_center
			doc.append("category_lines", line)
		doc.insert()
		if submit:
			doc.submit()
		return doc

	def _get_gl_entries(self, voucher_no):
		gle = qb.DocType("GL Entry")
		return (
			qb.from_(gle)
			.select(
				gle.account,
				gle.debit,
				gle.credit,
				gle.against,
				gle.voucher_subtype,
				gle.is_cancelled,
			)
			.where((gle.voucher_type == "Easy Cash Entry") & (gle.voucher_no == voucher_no))
			.orderby(gle.account, gle.debit, gle.credit)
			.run(as_dict=True)
		)

	def _check_gl_entries(self, voucher_no, expected):
		gl_entries = self._get_gl_entries(voucher_no)
		active = [g for g in gl_entries if not g.is_cancelled]
		active.sort(key=lambda x: (x.account, x.debit, x.credit))
		self.assertEqual(
			len(active),
			len(expected),
			f"Expected {len(expected)} GL entries, got {len(active)}: {active}",
		)
		for i, exp in enumerate(expected):
			for field in ["account", "debit", "credit"]:
				self.assertEqual(
					flt(active[i][field], 2),
					flt(exp[field], 2),
					f"Row {i} {field}: expected {exp[field]}, got {active[i][field]}",
				)

	# ---- GL Entry Tests ----

	def test_cash_in_creates_gl_entries(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 500}],
			submit=True,
		)
		self._check_gl_entries(
			doc.name,
			[
				{"account": self.cash_account, "debit": 500, "credit": 0},
				{"account": self.income_account, "debit": 0, "credit": 500},
			],
		)

	def test_cash_out_creates_gl_entries(self):
		doc = self._create_entry(
			entry_type="Cash Out",
			lines=[{"category": "Test Admin Expenses", "amount": 300}],
			submit=True,
		)
		self._check_gl_entries(
			doc.name,
			[
				{"account": self.expense_account, "debit": 300, "credit": 0},
				{"account": self.cash_account, "debit": 0, "credit": 300},
			],
		)

	def test_voucher_subtype_set(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 100}],
			submit=True,
		)
		for gle in self._get_gl_entries(doc.name):
			if not gle.is_cancelled:
				self.assertEqual(gle.voucher_subtype, "Cash In")

	def test_against_account_populated(self):
		doc = self._create_entry(
			entry_type="Cash Out",
			lines=[{"category": "Test Admin Expenses", "amount": 100}],
			submit=True,
		)
		active = [g for g in self._get_gl_entries(doc.name) if not g.is_cancelled]
		expense = [g for g in active if g.account == self.expense_account][0]
		self.assertEqual(expense.against, self.cash_account)
		cash = [g for g in active if g.account == self.cash_account][0]
		self.assertIn(self.expense_account, cash.against)

	# ---- Multiple Lines ----

	def test_multiple_category_lines(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[
				{"category": "Test Sales Revenue", "amount": 300},
				{"category": "Test Sales Revenue", "amount": 200},
			],
			submit=True,
		)
		self.assertEqual(flt(doc.total_amount), 500)
		self._check_gl_entries(
			doc.name,
			[
				{"account": self.cash_account, "debit": 500, "credit": 0},
				{"account": self.income_account, "debit": 0, "credit": 500},
			],
		)

	# ---- Cancellation ----

	def test_cancel_reverses_gl_entries(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 400}],
			submit=True,
		)
		active_before = [g for g in self._get_gl_entries(doc.name) if not g.is_cancelled]
		self.assertEqual(len(active_before), 2)

		doc.cancel()

		active_after = [g for g in self._get_gl_entries(doc.name) if not g.is_cancelled]
		self.assertEqual(len(active_after), 0)
		self.assertEqual(len(self._get_gl_entries(doc.name)), 4)

	def test_cancel_swaps_debit_credit(self):
		doc = self._create_entry(
			entry_type="Cash Out",
			lines=[{"category": "Test Admin Expenses", "amount": 250}],
			submit=True,
		)
		doc.cancel()

		reversing = [g for g in self._get_gl_entries(doc.name) if g.is_cancelled]
		expense_rev = [g for g in reversing if g.account == self.expense_account][0]
		self.assertEqual(flt(expense_rev.debit, 2), 0)
		self.assertEqual(flt(expense_rev.credit, 2), 250)

	# ---- Validations ----

	def test_category_type_mismatch_rejected(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._create_entry(
				entry_type="Cash In",
				lines=[{"category": "Test Admin Expenses", "amount": 100}],
			)
		self.assertIn("Cash Out", str(ctx.exception))

	def test_zero_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._create_entry(
				entry_type="Cash In",
				lines=[{"category": "Test Sales Revenue", "amount": 0}],
			)
		self.assertIn("greater than zero", str(ctx.exception))

	def test_negative_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._create_entry(
				entry_type="Cash In",
				lines=[{"category": "Test Sales Revenue", "amount": -50}],
			)
		self.assertIn("greater than zero", str(ctx.exception))

	def test_no_lines_rejected(self):
		doc = frappe.new_doc("Easy Cash Entry")
		doc.company = self.company
		doc.entry_type = "Cash In"
		doc.posting_date = nowdate()
		doc.treasury = "Test Treasury"
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.insert()
		self.assertIn("at least one", str(ctx.exception).lower())

	# ---- Auto-fill ----

	def test_currency_from_treasury(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 100}],
		)
		self.assertEqual(doc.currency, "EGP")

	def test_cash_account_from_treasury(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 100}],
		)
		self.assertEqual(doc.cash_account, self.cash_account)

	def test_remarks_auto_generated(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[{"category": "Test Sales Revenue", "amount": 100}],
			submit=True,
		)
		self.assertIn("Cash In", doc.remarks)
		self.assertIn(doc.name, doc.remarks)

	def test_total_amount_calculated(self):
		doc = self._create_entry(
			entry_type="Cash In",
			lines=[
				{"category": "Test Sales Revenue", "amount": 150},
				{"category": "Test Sales Revenue", "amount": 350},
			],
		)
		self.assertEqual(flt(doc.total_amount), 500)
