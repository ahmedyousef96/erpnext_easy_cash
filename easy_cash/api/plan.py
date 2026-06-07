import frappe
from frappe import _
from frappe.integrations.utils import make_post_request

USE_PLAN_LIMITS = False  # TODO: Enable after FC fixes sk_ key injection bug

PLAN_LIMITS = {
	"Free": 1,
	"Standard": 5,
	"Pro": float("inf"),
}

UNLIMITED = float("inf")

FC_API_URL = "https://frappecloud.com/api/method/press.api.developer.marketplace.get_subscription_info"

WHATSAPP = "+201028171836"


def get_secret_key():
	return frappe.conf.get("sk_easy_cash")


def get_subscription_plan():
	from frappe.utils.frappecloud import on_frappecloud

	secret_key = get_secret_key()

	if secret_key:
		try:
			response = make_post_request(
				FC_API_URL,
				data={"secret_key": secret_key},
			)
			plan = response.get("message", {}).get("plan", "")

			if plan and plan in PLAN_LIMITS:
				return plan

			frappe.log_error(
				"Easy Cash: Unexpected plan name from API: '{}'".format(plan),
				"Easy Cash Plan Check",
			)

		except Exception as e:
			frappe.log_error(
				"Easy Cash: API call failed: {}".format(e),
				"Easy Cash Plan Check",
			)

	if on_frappecloud():
		return "Free"

	return None


def get_treasury_limit(plan=None):
	if plan is None:
		plan = get_subscription_plan()
	if not plan:
		return UNLIMITED
	return PLAN_LIMITS.get(plan, UNLIMITED)


def get_treasury_count(company):
	return frappe.db.count("Treasury", {"company": company, "disabled": 0})


def validate_treasury_limit(company):
	if not USE_PLAN_LIMITS:
		return
	plan = get_subscription_plan()
	if not plan:
		return

	limit = get_treasury_limit(plan)
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

	count = get_treasury_count(company)

	if not USE_PLAN_LIMITS:
		return {
			"plan_enabled": False,
		}

	plan = get_subscription_plan()
	if not plan:
		plan = "Self-Hosted"

	limit = get_treasury_limit(plan)
	count = get_treasury_count(company)

	if limit == UNLIMITED:
		max_str = "Unlimited"
		remaining = "Unlimited"
	else:
		max_str = str(int(limit))
		remaining = str(max(0, int(limit) - count))

	return {
		"plan_enabled": True,
		"plan": plan,
		"max_treasuries": max_str,
		"current_treasuries": count,
		"remaining": remaining,
	}
