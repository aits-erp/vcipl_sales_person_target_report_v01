
(() => {
    const report_name = "Ageing - Customers";

    function set_current_date() {
        const config = frappe.query_reports[report_name];

        if (!config || config._current_date_hooked) {
            return;
        }

        const original_onload = config.onload;

        config.onload = function(report) {
            if (original_onload) {
                original_onload.apply(this, arguments);
            }

            report.set_filter_value(
                "report_date",
                frappe.datetime.get_today()
            );
        };

        config._current_date_hooked = true;
    }

    // Attach after the report configuration becomes available.
    frappe.router.on("change", set_current_date);
    set_current_date();
})();
