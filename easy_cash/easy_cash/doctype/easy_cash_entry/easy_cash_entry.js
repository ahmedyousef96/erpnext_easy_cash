frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("Easy Cash Entry", {
    setup: function (frm) {
        frm.set_query("treasury", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    disabled: 0,
                },
            };
        });
        frm.set_query("project", "category_lines", function () {
            return {
                filters: {
                    company: frm.doc.company,
                },
            };
        });
        erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
    },

    company: function (frm) {
        frm.set_value("cash_account", "");
        frm.set_value("treasury", "");
        frm.set_value("total_amount", 0);
        frm.doc.category_lines = [];
        frm.refresh_field("category_lines");
        if (frm.doc.company) {
            frappe.db
                .get_value("Company", frm.doc.company, [
                    "default_currency",
                    "cost_center",
                ])
                .then(function (r) {
                    if (r && r.message) {
                        frm.set_value("currency", r.message.default_currency);
                    }
                });
        }
        frm.trigger("set_category_filters");
        erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
    },

    entry_type: function (frm) {
        frm.trigger("set_category_filters");
        frm.set_value("total_amount", 0);
        frm.doc.category_lines = [];
        frm.refresh_field("category_lines");
    },

    treasury: function (frm) {
        if (!frm.doc.treasury && frm.doc.company) {
            frappe.db
                .get_value("Company", frm.doc.company, "default_currency")
                .then(function (r) {
                    if (r && r.message) {
                        frm.set_value("currency", r.message.default_currency);
                    }
                });
        }
    },

    set_category_filters: function (frm) {
        var entry_type = frm.doc.entry_type;
        frm.set_query("category", "category_lines", function () {
            return {
                filters: {
                    type: entry_type,
                    company: frm.doc.company,
                    disabled: 0,
                },
            };
        });
    },

    refresh: function (frm) {
        frm.trigger("set_category_filters");
        if (frm.doc.docstatus === 1 && !frm.doc.__islocal) {
            frm.add_custom_button(__("View General Ledger"), function () {
                frappe.set_route("query-report", "General Ledger", {
                    voucher_no: frm.doc.name,
                    company: frm.doc.company,
                });
            });
        }
    },
});

frappe.ui.form.on("Easy Cash Entry Detail", {
    category_lines_add: function (frm, cdt, cdn) {
        erpnext.accounts.dimensions.copy_dimension_from_first_row(
            frm,
            cdt,
            cdn,
            "category_lines"
        );
    },

    amount: function (frm, cdt, cdn) {
        calculate_total(frm);
    },

    category_lines_remove: function (frm) {
        calculate_total(frm);
    },
});

function calculate_total(frm) {
    var total = 0;
    for (var i = 0; i < frm.doc.category_lines.length; i++) {
        total += frm.doc.category_lines[i].amount || 0;
    }
    frm.set_value("total_amount", total);
}
