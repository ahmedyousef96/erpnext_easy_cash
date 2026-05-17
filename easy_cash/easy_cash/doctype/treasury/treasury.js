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
    },
});
