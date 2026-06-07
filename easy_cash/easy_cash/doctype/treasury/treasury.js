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
        frm.trigger("show_plan_info");
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
        frm.trigger("show_plan_info");
    },

    show_plan_info: function (frm) {
        if (!frm.doc.company) return;
        frappe.call({
            method: "easy_cash.api.plan.get_plan_info",
            args: { company: frm.doc.company },
            callback: function (r) {
                $(frm.wrapper).find(".ec-plan-info").remove();
                if (!r.message || !r.message.plan_enabled) return;
                var info = r.message;
                var color =
                    info.plan === "Self-Hosted"
                        ? "var(--text-muted)"
                        : info.plan === "Free"
                          ? "var(--orange)"
                          : "var(--primary)";
                var html =
                    '<div class="ec-plan-info" style="' +
                    "background: var(--bg-color);" +
                    "border: 1px solid var(--border-color);" +
                    "border-radius: var(--border-radius);" +
                    "padding: 8px 12px;" +
                    "margin-bottom: 15px;" +
                    "font-size: 12px;" +
                    "color: " +
                    color +
                    ";" +
                    '">' +
                    "<strong>Easy Cash Plan:</strong> " +
                    __(info.plan) +
                    " &nbsp;|&nbsp; " +
                    __("Treasuries") +
                    ": " +
                    info.current_treasuries +
                    "/" +
                    info.max_treasuries +
                    "</div>";
                $(frm.wrapper).find(".form-layout").prepend(html);
            },
        });
    },
});
