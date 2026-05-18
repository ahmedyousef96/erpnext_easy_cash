frappe.query_reports["Easy Cash Entry Register"] = {
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
		{
			fieldname: "category",
			label: __("Category"),
			fieldtype: "Link",
			options: "Easy Cash Category",
			get_query: function () {
				var company = frappe.query_report.get_filter_value("company");
				var entry_type = frappe.query_report.get_filter_value("entry_type");
				var filters = { company: company };
				if (entry_type) {
					filters.type = entry_type;
				}
				return { filters: filters };
			},
		},
	],
	tree: true,
	name_field: "name",
	parent_field: "parent_entry",
	initial_depth: 2,
	formatter: function (value, row, column, data, default_formatter) {
		if (!data) return default_formatter(value, row, column, data);

		value = default_formatter(value, row, column, data);
		if (data.indent == 0) {
			return $("<span></span>").html(value).css("font-weight", "bold").wrap("<p></p>").parent().html();
		}
		return value;
	},
};
