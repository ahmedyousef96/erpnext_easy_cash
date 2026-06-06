import frappe
import requests
from frappe import _

PLAN_LIMITS = {
	"Free": 1,
	"Standard": 5,
	"Pro": float("inf"),
}

UNLIMITED = float("inf")

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
		response.raise_for_status()
		data = response.json()
		plan = data.get("message", {}).get("plan", "")
		if not plan or plan not in PLAN_LIMITS:
			frappe.log_error(
				"Easy Cash: Unexpected plan name from API: {}".format(plan),
				"Easy Cash Plan Check",
			)
			return None
		frappe.cache.set_value(CACHE_KEY, plan, expires_in_sec=CACHE_TTL)
		return plan
	except Exception as e:
		frappe.log_error(
			"Easy Cash: Failed to verify subscription plan: {}".format(e),
			"Easy Cash Plan Check",
		)
		return None


def get_treasury_limit():
	plan = get_subscription_plan()
	if not plan:
		return UNLIMITED
	return PLAN_LIMITS.get(plan, UNLIMITED)


def get_treasury_count(company):
	return frappe.db.count("Treasury", {"company": company, "disabled": 0})


def validate_treasury_limit(company):
	plan = get_subscription_plan()
	if not plan:
		return

	limit = get_treasury_limit()
	if limit == UNLIMITED:
		return

	count = get_treasury_count(company)
	if count >= limit:
		frappe.throw(
			_(
				"You've reached the treasury limit for your {0} plan ({1}/{2}). "
				"To add more treasuries, upgrade your plan or contact us on WhatsApp: {3}"
			).format(plan, count, int(limit), WHATSAPP),
			title=_("Treasury Limit Reached"),
		)


@frappe.whitelist()
def get_plan_info(company):
	if not frappe.has_permission("Company", ptype="read", doc=company):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	plan = get_subscription_plan()
	if not plan:
		plan = "Self-Hosted"

	limit = get_treasury_limit()
	count = get_treasury_count(company)

	if limit == UNLIMITED:
		max_str = "Unlimited"
		remaining = "Unlimited"
	else:
		max_str = str(int(limit))
		remaining = str(max(0, int(limit) - count))

	return {
		"plan": plan,
		"max_treasuries": max_str,
		"current_treasuries": count,
		"remaining": remaining,
	}
