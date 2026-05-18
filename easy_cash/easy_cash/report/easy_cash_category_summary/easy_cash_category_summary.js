frappe.query_reports["Easy Cash Category Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "entry_type",
			label: __("Entry Type"),
			fieldtype: "Select",
			options: ["", "Cash In", "Cash Out"],
			default: "Cash Out",
			reqd: 1,
		},
		{
			fieldname: "treasury",
			label: __("Treasury"),
			fieldtype: "Link",
			options: "Treasury",
			get_query: function () {
				var company = frappe.query_report.get_filter_value("company");
				return { filters: { company: company } };
			},
		},
	],
};
