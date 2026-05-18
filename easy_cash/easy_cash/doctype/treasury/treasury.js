frappe.ui.form.on("Treasury", {
    company: function (frm) {
        frm.set_query("account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    account_type: ["in", ["Cash", "Bank"]],
                    is_group: 0,
                },
            };
        });
    },

    refresh: function (frm) {
        frm.trigger("company");
        if (!frm.is_new() && frm.doc.account) {
            frm.add_custom_button(__("View General Ledger"), function () {
                frappe.set_route("query-report", "General Ledger", {
                    account: frm.doc.account,
                    company: frm.doc.company,
                });
            });
        }
    },
});
