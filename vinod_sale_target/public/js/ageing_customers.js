
(() => {
    const report_name = "Ageing - Customers";

    function apply_current_date() {
        const report_config = frappe.query_reports[report_name];

        if (!report_config || report_config._current_date_applied) {
            return;
        }

        const original_onload = report_config.onload;

        report_config.onload = function(report) {
            if (original_onload) {
                original_onload(report);
            }

            report.set_filter_value(
                "report_date",
                frappe.datetime.get_today()
            );
        };

        report_config._current_date_applied = true;
    }

    apply_current_date();
})();
