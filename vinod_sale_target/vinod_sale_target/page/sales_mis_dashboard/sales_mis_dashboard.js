frappe.pages["sales-mis-dashboard"].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vinod Cookware — Performance Dashboard",
        single_column: true
    });

    let from_date = frappe.datetime.month_start();
    let to_date = frappe.datetime.month_end();

    $(page.body).html(`
        <style>
            .mis-wrap { padding: 18px; background: #f6f8fb; }
            .mis-header {
                background: #0b6a57;
                color: white;
                padding: 14px 18px;
                border-radius: 8px;
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 15px;
            }
            .mis-kpis {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 14px;
                margin-bottom: 18px;
            }
            .kpi {
                background: white;
                border-radius: 10px;
                padding: 16px;
                box-shadow: 0 3px 10px rgba(0,0,0,.08);
                border-left: 6px solid #0b6a57;
            }
            .kpi .label { font-size: 13px; color: #666; }
            .kpi .value { font-size: 22px; font-weight: 700; margin-top: 6px; }
            .mis-grid {
                display: grid;
                grid-template-columns: 38% 62%;
                gap: 15px;
            }
            .panel {
                background: white;
                border-radius: 10px;
                padding: 14px;
                box-shadow: 0 3px 10px rgba(0,0,0,.08);
                margin-bottom: 15px;
            }
            .panel-title {
                font-weight: 700;
                color: #0b3d5c;
                margin-bottom: 10px;
                font-size: 15px;
            }
            table.mis-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }
            .mis-table th {
                background: #0b3d5c;
                color: white;
                padding: 7px;
                border: 1px solid #ddd;
                text-align: center;
            }
            .mis-table td {
                padding: 6px;
                border: 1px solid #ddd;
            }
            .target { background: #fff2cc; text-align: right; }
            .achieved { background: #ddebf7; text-align: right; }
            .gap { background: #fce4d6; text-align: right; }
            .percent { background: #e2f0d9; text-align: right; font-weight: 700; }
            .section-buttons {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 10px;
                margin-bottom: 15px;
            }
            .sec-btn {
                padding: 14px;
                border-radius: 9px;
                color: white;
                font-weight: 700;
                cursor: pointer;
                text-align: center;
                box-shadow: 0 3px 10px rgba(0,0,0,.12);
            }
            .green { background: #0b6a57; }
            .blue { background: #1f4e78; }
            .orange { background: #c65d00; }
            .purple { background: #5b2c83; }
            .red { background: #922b21; }
        </style>

        <div class="mis-wrap">
            <div class="mis-header">Vinod Cookware — Q1 Performance Dashboard</div>

            <div class="section-buttons">
                <div class="sec-btn green" data-view="TSO Summary">TSO Summary</div>
                <div class="sec-btn blue" data-view="Region Summary">Region Summary</div>
                <div class="sec-btn purple" data-view="Mumbai AH Detail">Mumbai AH</div>
                <div class="sec-btn orange" data-view="ROM Detail">ROM</div>
                <div class="sec-btn red" data-view="Gujarat Detail">Gujarat</div>
            </div>

            <div class="mis-kpis">
                <div class="kpi"><div class="label">Total Target</div><div class="value" id="total-target">0</div></div>
                <div class="kpi"><div class="label">Total Achieved</div><div class="value" id="total-achieved">0</div></div>
                <div class="kpi"><div class="label">Not Achieved</div><div class="value" id="total-gap">0</div></div>
                <div class="kpi"><div class="label">Achievement %</div><div class="value" id="total-achievement">0%</div></div>
            </div>

            <div class="mis-grid">
                <div>
                    <div class="panel">
                        <div class="panel-title">Chart 1 — Category-wise: Achieved vs Gap</div>
                        <table class="mis-table" id="category-table"></table>
                    </div>

                    <div class="panel">
                        <div class="panel-title">Chart 2 — Area-wise: Achieved vs Gap</div>
                        <table class="mis-table" id="area-table"></table>
                    </div>

                    <div class="panel">
                        <div class="panel-title">Gap Summary — Total Not Achieved by Area</div>
                        <table class="mis-table" id="gap-table"></table>
                    </div>
                </div>

                <div>
                    <div class="panel">
                        <div id="category-chart"></div>
                    </div>

                    <div class="panel">
                        <div id="area-chart"></div>
                    </div>
                </div>
            </div>
        </div>
    `);

    function money(v) {
        return format_currency(v || 0, "INR");
    }

    function pct(v) {
        return (v || 0).toFixed(1) + "%";
    }

    function open_report(view_type) {
        frappe.set_route("query-report", "TEST REPORT", {
            from_date: from_date,
            to_date: to_date,
            customer_group: "Debtors Distributors",
            view_type: view_type
        });
    }

    $(page.body).find(".sec-btn").on("click", function() {
        open_report($(this).data("view"));
    });

    frappe.call({
        method: "vinod_sale_target.vinod_sale_target.report.test_report.test_report.get_mis_dashboard_data",
        args: {
            from_date: from_date,
            to_date: to_date
        },
        callback: function(r) {
            let d = r.message;

            $("#total-target").text(money(d.total_target));
            $("#total-achieved").text(money(d.total_achieved));
            $("#total-gap").text(money(d.total_gap));
            $("#total-achievement").text(pct(d.total_achievement));

            render_category_table(d.category_summary);
            render_area_table(d.area_summary);
            render_gap_table(d.area_summary);
            render_charts(d.category_summary, d.area_summary);
        }
    });

    function render_category_table(rows) {
        let html = `
            <tr>
                <th>Category</th>
                <th>Target</th>
                <th>Achieved</th>
                <th>Gap</th>
                <th>%Ach</th>
            </tr>
        `;

        rows.forEach(r => {
            html += `
                <tr>
                    <td>${r.category}</td>
                    <td class="target">${money(r.target)}</td>
                    <td class="achieved">${money(r.achieved)}</td>
                    <td class="gap">${money(r.gap)}</td>
                    <td class="percent">${pct(r.achievement)}</td>
                </tr>
            `;
        });

        $("#category-table").html(html);
    }

    function render_area_table(rows) {
        let html = `
            <tr>
                <th>Area</th>
                <th>Target</th>
                <th>Achieved</th>
                <th>Gap</th>
                <th>%Ach</th>
            </tr>
        `;

        rows.forEach(r => {
            html += `
                <tr>
                    <td>${r.area}</td>
                    <td class="target">${money(r.target)}</td>
                    <td class="achieved">${money(r.achieved)}</td>
                    <td class="gap">${money(r.gap)}</td>
                    <td class="percent">${pct(r.achievement)}</td>
                </tr>
            `;
        });

        $("#area-table").html(html);
    }

    function render_gap_table(rows) {
        rows = rows.slice().sort((a, b) => b.gap - a.gap);

        let html = `
            <tr>
                <th>Area</th>
                <th>Target</th>
                <th>Achieved</th>
                <th>Gap</th>
                <th>%Ach</th>
            </tr>
        `;

        rows.forEach(r => {
            html += `
                <tr>
                    <td>${r.area}</td>
                    <td class="target">${money(r.target)}</td>
                    <td class="achieved">${money(r.achieved)}</td>
                    <td class="gap">${money(r.gap)}</td>
                    <td class="percent">${pct(r.achievement)}</td>
                </tr>
            `;
        });

        $("#gap-table").html(html);
    }

    function render_charts(category_rows, area_rows) {
        new frappe.Chart("#category-chart", {
            title: "Category — Achieved vs Gap",
            data: {
                labels: category_rows.map(r => r.category),
                datasets: [
                    { name: "Achieved", values: category_rows.map(r => r.achieved) },
                    { name: "Not Achieved", values: category_rows.map(r => Math.max(r.gap, 0)) }
                ]
            },
            type: "bar",
            height: 280,
            colors: ["#4F81BD", "#C0504D"]
        });

        new frappe.Chart("#area-chart", {
            title: "Area — Achieved vs Gap",
            data: {
                labels: area_rows.map(r => r.area),
                datasets: [
                    { name: "Achieved", values: area_rows.map(r => r.achieved) },
                    { name: "Not Achieved", values: area_rows.map(r => Math.max(r.gap, 0)) }
                ]
            },
            type: "bar",
            height: 320,
            colors: ["#4F81BD", "#C0504D"]
        });
    }
};