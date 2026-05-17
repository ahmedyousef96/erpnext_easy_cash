frappe.ui.form.on("Easy Cash Category", {
    company: function (frm) {
        frm.set_query("account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0,
                },
            };
        });
    },
    refresh: function (frm) {
        frm.trigger("company");
    },
});
