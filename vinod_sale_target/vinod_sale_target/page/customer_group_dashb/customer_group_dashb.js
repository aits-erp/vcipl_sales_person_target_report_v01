frappe.pages["customer-group-dashb"].on_page_load = function (wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vinod Cookware — Customer Group MIS",
        single_column: true
    });

    // >>> CHANGED: points to the new Customer Group Report (was test_report)
    const REPORT_METHOD = "vinod_sale_target.vinod_sale_target.report.customer_group_report.customer_group_report";
    const REPORT_NAME = "Customer Group Report";

    // ------------------------------------------------------------------
    // Date helpers
    // ------------------------------------------------------------------
    function fmt_date(d) {
        let m = ("0" + (d.getMonth() + 1)).slice(-2);
        let dd = ("0" + d.getDate()).slice(-2);
        return d.getFullYear() + "-" + m + "-" + dd;
    }

    function get_fy_quarter_dates(quarter, fy_start_year) {
        let ranges = {
            1: { start_month: 4, end_month: 6, year: fy_start_year },
            2: { start_month: 7, end_month: 9, year: fy_start_year },
            3: { start_month: 10, end_month: 12, year: fy_start_year },
            4: { start_month: 1, end_month: 3, year: fy_start_year + 1 }
        };
        let r = ranges[quarter];
        let start = new Date(r.year, r.start_month - 1, 1);
        let end = new Date(r.year, r.end_month, 0);
        return { from_date: fmt_date(start), to_date: fmt_date(end) };
    }

    function get_current_fy_quarter() {
        let today = new Date();
        let month = today.getMonth() + 1;
        let year = today.getFullYear();
        if (month >= 4 && month <= 6) return { quarter: 1, fy_start_year: year };
        if (month >= 7 && month <= 9) return { quarter: 2, fy_start_year: year };
        if (month >= 10 && month <= 12) return { quarter: 3, fy_start_year: year };
        return { quarter: 4, fy_start_year: year - 1 };
    }

    function quarter_label(quarter, fy_start_year) {
        return "Q" + quarter + " (FY " + fy_start_year + "-" + String(fy_start_year + 1).slice(-2) + ")";
    }

    function get_month_dates(month, fy_start_year) {
        let year = month >= 4 ? fy_start_year : fy_start_year + 1;
        let start = new Date(year, month - 1, 1);
        let end = new Date(year, month, 0);
        return { from_date: fmt_date(start), to_date: fmt_date(end), year: year };
    }

    // ------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------
    const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    let current = get_current_fy_quarter();
    let selected_quarter = current.quarter;
    let selected_fy_start_year = current.fy_start_year;
    let selected_month = null;
    let selected_customer_group = "All Customer Groups";   // default tab

    let dates = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
    let from_date = dates.from_date;
    let to_date = dates.to_date;

    let this_calendar_year = new Date().getFullYear();
    let fy_options = [];
    for (let y = this_calendar_year - 5; y <= this_calendar_year + 5; y++) fy_options.push(y);

    let _last_category_data = [];
    let _last_area_data = [];
    let _last_region_cat = {};

    // ------------------------------------------------------------------
    // Layout
    // ------------------------------------------------------------------
    $(page.body).html(`
        <style>
            .mis-wrap { padding: 18px; background: #f5f7fb; }

            .mis-header {
                background: linear-gradient(135deg, #064e3b, #0f766e);
                color: white; padding: 18px 22px; border-radius: 12px;
                font-size: 22px; font-weight: 800; margin-bottom: 14px;
                box-shadow: 0 6px 18px rgba(0,0,0,.12);
            }
            .mis-subtitle { font-size: 13px; font-weight: 400; opacity: .9; margin-top: 5px; }

            .mis-quarter-bar {
                background: white; border-radius: 12px; padding: 12px 16px;
                box-shadow: 0 4px 14px rgba(0,0,0,.08); margin-bottom: 18px;
                display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
            }
            .mis-quarter-bar .quarter-current-label { font-weight: 800; color: #0b3d5c; font-size: 14px; margin-right: 6px; }
            .mis-quarter-bar select { padding: 6px 10px; border-radius: 8px; border: 1px solid #cbd5e1; font-weight: 600; color: #1e293b; }

            .quarter-btns { display: flex; gap: 8px; }
            .quarter-btn {
                padding: 7px 16px; border-radius: 8px; border: 1px solid #0f766e;
                background: white; color: #0f766e; font-weight: 700; cursor: pointer;
                font-size: 13px; transition: all .15s ease;
            }
            .quarter-btn:hover { background: #e6f4f1; }
            .quarter-btn.active { background: #0f766e; color: white; }

            .custom-range-bar {
                display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
                padding: 10px 16px; background: #f0fdf4; border-radius: 10px;
                border: 1px solid #bbf7d0; margin-top: 4px; width: 100%;
            }
            .custom-range-bar label { font-weight: 700; color: #0b3d5c; font-size: 13px; }
            .custom-range-bar input[type="date"] {
                padding: 5px 8px; border-radius: 8px; border: 1px solid #cbd5e1;
                font-weight: 600; color: #1e293b; font-size: 12px;
            }
            .custom-range-bar button {
                padding: 6px 16px; border-radius: 8px; background: #0f766e;
                color: white; border: none; font-weight: 700; cursor: pointer;
                font-size: 12px; transition: background .15s;
            }
            .custom-range-bar button:hover { background: #064e3b; }

            .quarter-range-label { font-size: 12px; color: #64748b; font-weight: 600; margin-left: auto; }

            .month-bar {
                display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
                padding: 10px 16px; background: #f8fafc; border-radius: 10px;
                border: 1px solid #e2e8f0; margin-top: 4px; width: 100%;
            }
            .month-bar label { font-weight: 700; color: #0b3d5c; font-size: 13px; }
            .month-btns { display: flex; gap: 6px; flex-wrap: wrap; }
            .month-btn {
                padding: 5px 12px; border-radius: 8px; border: 1px solid #0f766e;
                background: white; color: #0f766e; font-weight: 700; cursor: pointer;
                font-size: 12px; transition: all .15s ease;
            }
            .month-btn:hover { background: #e6f4f1; }
            .month-btn.active { background: #0f766e; color: white; }

            .mis-section-title { font-size: 16px; font-weight: 800; color: #0b3d5c; margin: 18px 0 10px; }

            /* ---------- Customer Group tabs (green, 6 per row) ---------- */
            .cg-tabs {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 10px; margin-bottom: 18px;
            }
            .cg-tab {
                padding: 10px 12px; border-radius: 10px; color: white; font-weight: 800;
                font-size: 13px; cursor: pointer; text-align: center;
                min-height: 42px; display: flex; align-items: center; justify-content: center;
                background: linear-gradient(135deg, #047857, #10b981);
                box-shadow: 0 4px 10px rgba(0,0,0,.15); transition: all .2s ease;
                opacity: .75;
            }
            .cg-tab:hover { transform: translateY(-2px); opacity: 1; }
            .cg-tab.active { opacity: 1; outline: 3px solid #0b3d5c; box-shadow: 0 8px 20px rgba(0,0,0,.25); }
            /* parent groups (include their child groups) = same dark green as the header */
            .cg-tab.cg-parent { background: linear-gradient(135deg, #064e3b, #0f766e); }

            .mis-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 18px; }
            .kpi-card { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 4px 14px rgba(0,0,0,.08); border-left: 6px solid #0f766e; }
            .kpi-label { font-size: 13px; color: #64748b; font-weight: 600; }
            .kpi-value { font-size: 23px; font-weight: 800; margin-top: 6px; color: #1e293b; }

            .mis-grid { display: grid; grid-template-columns: 42% 58%; gap: 14px; }
            .panel { background: white; border-radius: 12px; padding: 14px; box-shadow: 0 4px 14px rgba(0,0,0,.08); margin-bottom: 14px; }
            .panel-title { font-weight: 800; color: #0b3d5c; margin-bottom: 10px; font-size: 14px; }

            table.mis-table { width: 100%; border-collapse: collapse; font-size: 12px; }
            .mis-table th { background: #0b3d5c; color: white; padding: 7px; border: 1px solid #ddd; text-align: center; }
            .mis-table td { padding: 6px; border: 1px solid #ddd; }
            .target   { background: #fff2cc; text-align: right; }
            .achieved { background: #ddebf7; text-align: right; }
            .gap      { background: #fce4d6; text-align: right; }
            .percent  { background: #e2f0d9; text-align: right; font-weight: 800; }

            .region-cat-filter { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
            .region-cat-filter select { padding: 5px 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 12px; font-weight: 600; color: #1e293b; }
            .region-cat-filter label { font-size: 12px; font-weight: 700; color: #0b3d5c; }

            @media (max-width: 1100px) {
                .cg-tabs { grid-template-columns: repeat(3, 1fr); }
            }
            @media (max-width: 900px) {
                .mis-grid { grid-template-columns: 1fr; }
                .quarter-range-label { margin-left: 0; }
            }
        </style>

        <div class="mis-wrap">
            <div class="mis-header">
                Vinod Cookware — <span id="header-quarter-label"></span> Performance Dashboard
                <div class="mis-subtitle">
                    Customer group: <b id="header-cg-label"></b>
                </div>
            </div>

            <div class="mis-quarter-bar">
                <span class="quarter-current-label">Financial Year</span>
                <select id="fy-select"></select>

                <div class="quarter-btns" id="quarter-btns">
                    <div class="quarter-btn" data-q="1">Q1 (Apr-Jun)</div>
                    <div class="quarter-btn" data-q="2">Q2 (Jul-Sep)</div>
                    <div class="quarter-btn" data-q="3">Q3 (Oct-Dec)</div>
                    <div class="quarter-btn" data-q="4">Q4 (Jan-Mar)</div>
                </div>

                <span class="quarter-range-label" id="quarter-range-label"></span>

                <div class="custom-range-bar">
                    <label>Custom Range:</label>
                    <input type="date" id="custom-from-date">
                    <span style="font-weight:600;color:#64748b;font-size:12px;">to</span>
                    <input type="date" id="custom-to-date">
                    <button id="apply-custom-range">Apply</button>
                    <span id="custom-range-active-label"
                          style="font-size:11px;color:#0f766e;font-weight:700;display:none;">
                        ✓ Custom range active
                    </span>
                </div>

                <div class="month-bar">
                    <label>Month:</label>
                    <div class="month-btns" id="month-btns"></div>
                </div>
            </div>

            <div class="mis-section-title">Customer Groups</div>
            <div class="cg-tabs" id="cg-tabs"></div>

            <div class="mis-kpis">
                <div class="kpi-card"><div class="kpi-label">Total Target</div><div class="kpi-value" id="total-target">0</div></div>
                <div class="kpi-card"><div class="kpi-label">Total Achieved</div><div class="kpi-value" id="total-achieved">0</div></div>
                <div class="kpi-card"><div class="kpi-label">Not Achieved</div><div class="kpi-value" id="total-gap">0</div></div>
                <div class="kpi-card"><div class="kpi-label">Achievement %</div><div class="kpi-value" id="total-achievement">0%</div></div>
            </div>

            <div class="mis-grid">
                <div>
                    <div class="panel">
                        <div class="panel-title">Chart 1 — Category-wise: Achieved vs Gap</div>
                        <table class="mis-table" id="category-table"></table>
                    </div>
                    <div class="panel">
                        <div class="panel-title">Gap Summary — Total Not Achieved by Area</div>
                        <table class="mis-table" id="gap-table"></table>
                    </div>
                </div>

                <div>
                    <div class="panel"><div id="category-chart"></div></div>
                    <div class="panel"><div id="area-chart"></div></div>
                    <div class="panel">
                        <div class="panel-title">Region × Category — Target vs Achieved</div>
                        <div class="region-cat-filter">
                            <label>Filter by Region:</label>
                            <select id="region-cat-region">
                                <option value="">All Regions</option>
                                <option value="North">North</option>
                                <option value="South">South</option>
                                <option value="East">East</option>
                                <option value="ROM">ROM</option>
                                <option value="Mumbai AH">Mumbai AH</option>
                                <option value="MPCG">MPCG</option>
                                <option value="Gujarat">Gujarat</option>
                            </select>
                        </div>
                        <div id="region-cat-chart"></div>
                        <table class="mis-table" id="region-cat-table" style="margin-top:12px;"></table>
                    </div>
                </div>
            </div>
        </div>
    `);

    // ------------------------------------------------------------------
    // Formatting
    // ------------------------------------------------------------------
    function money(v) { return format_currency(v || 0, "INR"); }
    function pct(v) { return (v || 0).toFixed(1) + "%"; }

    // ------------------------------------------------------------------
    // Open the Customer Group Report for a customer group
    // ------------------------------------------------------------------
    function open_report(customer_group) {
        frappe.set_route("query-report", REPORT_NAME, {
            from_date: from_date,
            to_date: to_date,
            customer_group: customer_group,
            view_type: "TSO Summary"
        });
    }

    // ------------------------------------------------------------------
    // Customer Group tabs
    // ------------------------------------------------------------------
    function render_cg_tabs(rows) {
        let $wrap = $(page.body).find("#cg-tabs").empty();

        rows.forEach(function (row) {
            let $t = $('<div class="cg-tab"></div>').text(row.name);
            if (row.is_group) $t.addClass("cg-parent");   // darker green = parent group (includes its children)
            if (row.name === selected_customer_group) $t.addClass("active");

            $t.on("click", function () {
                selected_customer_group = row.name;
                $wrap.find(".cg-tab").removeClass("active");
                $t.addClass("active");
                $(page.body).find("#header-cg-label").text(selected_customer_group);

                // refresh dashboard figures in the background (no freeze screen)
                load_dashboard_data(true);

                // and go straight to the report page
                open_report(row.name);
            });
            $wrap.append($t);
        });
    }

    function load_customer_group_tabs() {
        frappe.db.get_list("Customer Group", {
            fields: ["name", "is_group"],
            order_by: "lft asc",
            limit: 200
        }).then(function (rows) {
            if (!rows.length) return;
            let names = rows.map(r => r.name);
            if (!names.includes(selected_customer_group)) selected_customer_group = names[0];
            $(page.body).find("#header-cg-label").text(selected_customer_group);
            render_cg_tabs(rows);
        });
    }

    // ------------------------------------------------------------------
    // Financial year / quarter / month / custom range
    // ------------------------------------------------------------------
    let $fy_select = $(page.body).find("#fy-select");
    fy_options.forEach(y => {
        $fy_select.append(`<option value="${y}">FY ${y}-${String(y + 1).slice(-2)}</option>`);
    });
    $fy_select.val(selected_fy_start_year);

    let $month_btns = $(page.body).find("#month-btns");
    MONTH_NAMES.forEach(function (name, i) {
        $month_btns.append(`<div class="month-btn" data-m="${i + 1}">${name}</div>`);
    });

    function update_quarter_ui() {
        $(page.body).find(".quarter-btn, .month-btn").removeClass("active");
        let label;

        if (selected_month) {
            $(page.body).find(`.month-btn[data-m="${selected_month}"]`).addClass("active");
            let d = get_month_dates(selected_month, selected_fy_start_year);
            label = MONTH_NAMES[selected_month - 1] + "-" + d.year;
        } else {
            $(page.body).find(`.quarter-btn[data-q="${selected_quarter}"]`).addClass("active");
            label = quarter_label(selected_quarter, selected_fy_start_year);
        }

        $(page.body).find("#header-quarter-label").text(label);
        $(page.body).find("#quarter-range-label").text(
            frappe.datetime.str_to_user(from_date) + "  to  " + frappe.datetime.str_to_user(to_date)
        );
        $(page.body).find("#custom-range-active-label").hide();
    }

    function apply_quarter_change() {
        let d = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
        from_date = d.from_date;
        to_date = d.to_date;
        $(page.body).find("#custom-from-date").val(from_date);
        $(page.body).find("#custom-to-date").val(to_date);
        update_quarter_ui();
        load_dashboard_data();
    }

    function apply_month_change() {
        let d = get_month_dates(selected_month, selected_fy_start_year);
        from_date = d.from_date;
        to_date = d.to_date;
        $(page.body).find("#custom-from-date").val(from_date);
        $(page.body).find("#custom-to-date").val(to_date);
        update_quarter_ui();
        load_dashboard_data();
    }

    $(page.body).find(".quarter-btn").on("click", function () {
        selected_quarter = parseInt($(this).data("q"));
        selected_month = null;
        apply_quarter_change();
    });

    $(page.body).find(".month-btn").on("click", function () {
        selected_month = parseInt($(this).data("m"));
        selected_quarter = null;
        apply_month_change();
    });

    $fy_select.on("change", function () {
        selected_fy_start_year = parseInt($(this).val());
        if (selected_month) {
            apply_month_change();
        } else {
            if (!selected_quarter) selected_quarter = 1;
            apply_quarter_change();
        }
    });

    $(page.body).find("#custom-from-date").val(from_date);
    $(page.body).find("#custom-to-date").val(to_date);

    $(page.body).find("#apply-custom-range").on("click", function () {
        let f = $(page.body).find("#custom-from-date").val();
        let t = $(page.body).find("#custom-to-date").val();
        if (!f || !t) { frappe.msgprint("Please select both From and To dates."); return; }
        if (f > t) { frappe.msgprint("From date cannot be after To date."); return; }
        $(page.body).find(".quarter-btn, .month-btn").removeClass("active");
        selected_quarter = null;
        selected_month = null;
        from_date = f;
        to_date = t;
        $(page.body).find("#header-quarter-label").text("Custom Range");
        $(page.body).find("#quarter-range-label").text(
            frappe.datetime.str_to_user(from_date) + "  to  " + frappe.datetime.str_to_user(to_date)
        );
        $(page.body).find("#custom-range-active-label").show();
        load_dashboard_data();
    });

    $(page.body).find("#region-cat-region").on("change", function () {
        render_region_cat_chart(_last_category_data, _last_area_data);
    });

    // ------------------------------------------------------------------
    // Data loading
    // silent = true  -> no "loading" freeze screen (used when a tab opens the report)
    // ------------------------------------------------------------------
    function load_dashboard_data(silent) {
        frappe.call({
            method: REPORT_METHOD + ".get_mis_dashboard_data",
            args: {
                from_date: from_date,
                to_date: to_date,
                customer_group: selected_customer_group
            },
            freeze: !silent,
            freeze_message: __("Loading {0} ...", [selected_customer_group]),
            callback: function (r) {
                let d = r.message || {};
                let kpi = d.kpi || {};

                $(page.body).find("#total-target").text(money(kpi.target));
                $(page.body).find("#total-achieved").text(money(kpi.achieved));
                $(page.body).find("#total-gap").text(money(kpi.gap));
                $(page.body).find("#total-achievement").text(pct(kpi.achievement));

                _last_category_data = d.category_summary || [];
                _last_area_data = d.area_summary || [];
                _last_region_cat = d.region_category || {};

                render_category_table(_last_category_data);
                render_gap_table(_last_area_data);
                render_charts(_last_category_data, _last_area_data);
                render_region_cat_chart(_last_category_data, _last_area_data);
            },
            error: function (err) {
                frappe.msgprint("Dashboard data could not be loaded. Please check server error log.");
                console.error(err);
            }
        });
    }

    // ------------------------------------------------------------------
    // Renderers (sorted by achievement % descending)
    // ------------------------------------------------------------------
    function by_achievement(rows) {
        return rows.slice().sort((a, b) => (b.achievement || 0) - (a.achievement || 0));
    }

    function table_html(first_col_label, rows, key) {
        let html = `
            <tr>
                <th>${first_col_label}</th><th>Target</th><th>Achieved</th><th>Gap</th><th>%Ach</th>
            </tr>`;
        rows.forEach(r => {
            html += `
                <tr>
                    <td>${frappe.utils.escape_html(r[key] || "")}</td>
                    <td class="target">${money(r.target)}</td>
                    <td class="achieved">${money(r.achieved)}</td>
                    <td class="gap">${money(r.gap)}</td>
                    <td class="percent">${pct(r.achievement)}</td>
                </tr>`;
        });
        return html;
    }

    function render_category_table(rows) {
        $(page.body).find("#category-table").html(table_html("Category", by_achievement(rows), "category"));
    }

    function render_gap_table(rows) {
        $(page.body).find("#gap-table").html(table_html("Area", by_achievement(rows), "area"));
    }

    function render_charts(category_rows, area_rows) {
        $(page.body).find("#category-chart").empty();
        $(page.body).find("#area-chart").empty();

        let sorted_cat = by_achievement(category_rows);
        if (sorted_cat.length) {
            new frappe.Chart($(page.body).find("#category-chart")[0], {
                title: "Category — Achieved vs Gap",
                data: {
                    labels: sorted_cat.map(r => r.category),
                    datasets: [
                        { name: "Achieved", values: sorted_cat.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: sorted_cat.map(r => Math.max(r.gap || 0, 0)) }
                    ]
                },
                type: "bar",
                height: 300,
                colors: ["#4F81BD", "#C0504D"]
            });
        }

        let sorted_area = by_achievement(area_rows);
        if (sorted_area.length) {
            new frappe.Chart($(page.body).find("#area-chart")[0], {
                title: "Area — Achieved vs Gap",
                data: {
                    labels: sorted_area.map(r => r.area),
                    datasets: [
                        { name: "Achieved", values: sorted_area.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: sorted_area.map(r => Math.max(r.gap || 0, 0)) }
                    ]
                },
                type: "bar",
                height: 330,
                colors: ["#4F81BD", "#C0504D"]
            });
        }
    }

    function render_region_cat_chart(category_rows, area_rows) {
        let selected_region = $(page.body).find("#region-cat-region").val();

        let rows = category_rows;
        if (selected_region && _last_region_cat[selected_region]) {
            rows = _last_region_cat[selected_region];
        }
        let sorted = by_achievement(rows);

        $(page.body).find("#region-cat-chart").empty();
        if (sorted.length) {
            new frappe.Chart($(page.body).find("#region-cat-chart")[0], {
                title: selected_region
                    ? `${selected_region} — Category Target vs Achieved`
                    : "All Regions — Category Target vs Achieved",
                data: {
                    labels: sorted.map(r => r.category),
                    datasets: [
                        { name: "Target", values: sorted.map(r => r.target || 0) },
                        { name: "Achieved", values: sorted.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: sorted.map(r => Math.max((r.target || 0) - (r.achieved || 0), 0)) }
                    ]
                },
                type: "bar",
                height: 320,
                colors: ["#FFC107", "#4F81BD", "#C0504D"]
            });
        }

        let html = `
            <tr><th>Category</th><th>Target</th><th>Achieved</th><th>Gap</th><th>%Ach</th></tr>`;
        sorted.forEach(r => {
            let t = r.target || 0;
            let a = r.achieved || 0;
            let g = Math.max(t - a, 0);
            let p = t ? (a / t * 100) : 0;
            html += `
                <tr>
                    <td>${frappe.utils.escape_html(r.category || "")}</td>
                    <td class="target">${money(t)}</td>
                    <td class="achieved">${money(a)}</td>
                    <td class="gap">${money(g)}</td>
                    <td class="percent">${pct(p)}</td>
                </tr>`;
        });
        $(page.body).find("#region-cat-table").html(html);
    }

    // ------------------------------------------------------------------
    // Start
    // ------------------------------------------------------------------
    update_quarter_ui();
    load_customer_group_tabs();
    load_dashboard_data();
};