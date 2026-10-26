(() => {
    const REPORT_NAME = "Ageing - Customers";
    const WATCH_MS = 5000;   // how long to guard the date after opening
    const STEP_MS = 300;     // how often to re-check

    // prevent registering twice if the file is loaded again
    if (window.__ageing_today_hooked) return;
    window.__ageing_today_hooked = true;

    let run_id = 0;

    function is_this_report() {
        const route = frappe.get_route() || [];
        return route[0] === "query-report" &&
            decodeURIComponent(route[1] || "") === REPORT_NAME;
    }

    function filter_ready() {
        const qr = frappe.query_report;
        return !!(qr && qr.report_name === REPORT_NAME &&
            qr.get_filter && qr.get_filter("report_date"));
    }

    function apply_today() {
        const my_run = ++run_id;
        const started = Date.now();

        const timer = setInterval(() => {
            // stop if the user left the report, a newer run started, or time is up
            if (my_run !== run_id || !is_this_report() ||
                Date.now() - started > WATCH_MS) {
                clearInterval(timer);
                return;
            }
            if (!filter_ready()) return;

            const today = frappe.datetime.get_today();
            if (frappe.query_report.get_filter_value("report_date") !== today) {
                frappe.query_report.set_filter_value("report_date", today);
            }
        }, STEP_MS);
    }

    frappe.router.on("change", () => {
        if (is_this_report()) apply_today();
    });

    // in case the report is already open when this file loads
    if (is_this_report()) apply_today();
})();