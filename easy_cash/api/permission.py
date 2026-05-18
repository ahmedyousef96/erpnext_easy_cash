import frappe


def has_app_permission():
	return (
		"Accounts User" in frappe.get_roles()
		or "Accounts Manager" in frappe.get_roles()
		or "System Manager" in frappe.get_roles()
	)
