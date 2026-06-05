import frappe
import requests
from frappe import _

PLAN_LIMITS = {
	"Free": 1,
	"Standard": 5,
	"Pro": 999999,
}

FC_API_URL = "https://cloud.frappe.io/api/method/press.api.developer.marketplace.get_subscription_info"
CACHE_KEY = "easy_cash_subscription_plan"
CACHE_TTL = 3600

WHATSAPP = "+201028171836"


def get_secret_key():
	return frappe.conf.get("sk_easy_cash")


def get_subscription_plan():
	secret_key = get_secret_key()
	if not secret_key:
		return None

	cached = frappe.cache.get_value(CACHE_KEY)
	if cached:
		return cached

	try:
		response = requests.post(
			FC_API_URL,
			data={"secret_key": secret_key},
			timeout=10,
		)
		data = response.json()
		plan = data.get("message", {}).get("plan", "")
		frappe.cache.set_value(CACHE_KEY, plan, expires_in_sec=CACHE_TTL)
		return plan
	except Exception:
		return None


def get_treasury_limit(company):
	plan = get_subscription_plan()
	if not plan:
		return 999999
	return PLAN_LIMITS.get(plan, 999999)


def get_treasury_count(company):
	return frappe.db.count("Treasury", {"company": company})


def validate_treasury_limit(company):
	plan = get_subscription_plan()
	if not plan:
		return

	limit = get_treasury_limit(company)
	if limit >= 999999:
		return

	count = get_treasury_count(company)
	if count >= limit:
		frappe.throw(
			_(
				"You've reached the treasury limit for your {0} plan ({1}/{2}). "
				"To add more treasuries, upgrade your plan or contact us on WhatsApp: {3}"
			).format(plan, count, limit, WHATSAPP),
			title=_("Treasury Limit Reached"),
		)


@frappe.whitelist()
def get_plan_info(company):
	plan = get_subscription_plan()
	if not plan:
		plan = "Self-Hosted"

	limit = get_treasury_limit(company)
	count = get_treasury_count(company)

	if limit >= 999999:
		max_str = "Unlimited"
		remaining = "Unlimited"
	else:
		max_str = str(limit)
		remaining = str(max(0, limit - count))

	return {
		"plan": plan,
		"max_treasuries": max_str,
		"current_treasuries": count,
		"remaining": remaining,
	}
