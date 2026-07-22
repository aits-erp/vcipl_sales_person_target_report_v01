frappe.pages["sales-mis-dashboard"].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vinod Cookware — Sales MIS Dashboard",
        single_column: true
    });

    let from_date = frappe.datetime.month_start();
    let to_date = frappe.datetime.month_end();

    $(page.body).html(`
        <style>
            .mis-wrap {
                padding: 18px;
                background: #f5f7fb;
            }

            .mis-header {
                background: linear-gradient(135deg, #064e3b, #0f766e);
                color: white;
                padding: 18px 22px;
                border-radius: 12px;
                font-size: 22px;
                font-weight: 800;
                margin-bottom: 18px;
                box-shadow: 0 6px 18px rgba(0,0,0,.12);
            }

            .mis-subtitle {
                font-size: 13px;
                font-weight: 400;
                opacity: .9;
                margin-top: 5px;
            }

            .mis-section-title {
                font-size: 16px;
                font-weight: 800;
                color: #0b3d5c;
                margin: 18px 0 10px;
            }

            .mis-btn-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                gap: 12px;
                margin-bottom: 18px;
            }

            .mis-btn {
                padding: 15px 14px;
                border-radius: 12px;
                color: white;
                font-weight: 800;
                cursor: pointer;
                text-align: center;
                box-shadow: 0 6px 15px rgba(0,0,0,.15);
                transition: all .2s ease;
                min-height: 70px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
            }

            .mis-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0,0,0,.22);
            }

            .mis-btn small {
                font-size: 11px;
                opacity: .9;
                margin-top: 4px;
                font-weight: 600;
            }

            .green { background: linear-gradient(135deg, #047857, #10b981); }
            .blue { background: linear-gradient(135deg, #1d4ed8, #2563eb); }
            .purple { background: linear-gradient(135deg, #6b21a8, #9333ea); }
            .orange { background: linear-gradient(135deg, #c2410c, #f97316); }
            .red { background: linear-gradient(135deg, #991b1b, #dc2626); }
            .teal { background: linear-gradient(135deg, #0f766e, #14b8a6); }
            .dark { background: linear-gradient(135deg, #1f2937, #4b5563); }
            .pink { background: linear-gradient(135deg, #be185d, #ec4899); }
            .yellow { background: linear-gradient(135deg, #a16207, #eab308); }
            .black { background: linear-gradient(135deg, #111827, #0f766e); }

            .mis-kpis {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 14px;
                margin-bottom: 18px;
            }

            .kpi-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 4px 14px rgba(0,0,0,.08);
                border-left: 6px solid #0f766e;
            }

            .kpi-label {
                font-size: 13px;
                color: #64748b;
                font-weight: 600;
            }

            .kpi-value {
                font-size: 23px;
                font-weight: 800;
                margin-top: 6px;
                color: #1e293b;
            }

            .mis-grid {
                display: grid;
                grid-template-columns: 42% 58%;
                gap: 14px;
            }

            .panel {
                background: white;
                border-radius: 12px;
                padding: 14px;
                box-shadow: 0 4px 14px rgba(0,0,0,.08);
                margin-bottom: 14px;
            }

            .panel-title {
                font-weight: 800;
                color: #0b3d5c;
                margin-bottom: 10px;
                font-size: 14px;
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
            .percent { background: #e2f0d9; text-align: right; font-weight: 800; }

            @media(max-width: 900px) {
                .mis-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>

        <div class="mis-wrap">
            <div class="mis-header">
                Vinod Cookware — Q1 Performance Dashboard
                <div class="mis-subtitle">
                    One-click MIS dashboard with all worksheet sections and full Excel download.
                </div>
            </div>

            <div class="mis-section-title">Worksheet Reports</div>
            <div class="mis-btn-grid">

                <div class="mis-btn green" data-view="TSO Summary">
                    TSO Summary
                    <small>Distributor-wise target vs achievement</small>
                </div>

                <div class="mis-btn blue" data-view="Region Summary">
                    Region Summary
                    <small>Area-wise consolidated report</small>
                </div>

                <div class="mis-btn purple" id="charts-section">
                    Charts
                    <small>Category and area performance charts</small>
                </div>

                <div class="mis-btn pink" data-view="Mumbai AH Detail">
                    Mumbai AH Details
                    <small>TSOMUM1 to TSOMUM5</small>
                </div>

                <div class="mis-btn orange" data-view="ROM Detail">
                    ROM Details
                    <small>HSROM</small>
                </div>

                <div class="mis-btn yellow" data-view="MPCG Detail">
                    MPCG Details
                    <small>HSMPCG</small>
                </div>

                <div class="mis-btn red" data-view="Gujarat Detail">
                    Gujarat Details
                    <small>TSOSRT1</small>
                </div>

                <div class="mis-btn blue" data-view="North TSO Detail">
                    North TSO Details
                    <small>North region detail</small>
                </div>

                <div class="mis-btn teal" data-view="East TSO Detail">
                    East TSO Details
                    <small>East region detail</small>
                </div>

                <div class="mis-btn green" data-view="South TSO Detail">
                    South TSO Details
                    <small>South region detail</small>
                </div>
                
                
            

                <div class="mis-btn black" id="download-full-excel">
                    Download Full MIS Excel
                    <small>Download all worksheet reports</small>
                </div>

            </div>

            <div class="mis-kpis">
                <div class="kpi-card">
                    <div class="kpi-label">Total Target</div>
                    <div class="kpi-value" id="total-target">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Achieved</div>
                    <div class="kpi-value" id="total-achieved">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Not Achieved</div>
                    <div class="kpi-value" id="total-gap">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Achievement %</div>
                    <div class="kpi-value" id="total-achievement">0%</div>
                </div>
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

    $(page.body).find(".mis-btn[data-view]").on("click", function() {
        open_report($(this).data("view"));
    });

    $(page.body).find("#charts-section").on("click", function() {
        $("html, body").animate({
            scrollTop: $("#category-chart").offset().top - 120
        }, 400);
    });

    $(page.body).find("#download-full-excel").on("click", function() {
        let filters = {
            from_date: from_date,
            to_date: to_date,
            customer_group: "Debtors Distributors",
            view_type: "TSO Summary"
        };

        let query = new URLSearchParams(filters).toString();

        window.open(
            "/api/method/vinod_sale_target.vinod_sale_target.report.test_report.test_report.download_mis_excel?"
            + query
        );
    });

    frappe.call({
        method: "vinod_sale_target.vinod_sale_target.report.test_report.test_report.get_mis_dashboard_data",
        args: {
            from_date: from_date,
            to_date: to_date
        },
        callback: function(r) {
            let d = r.message || {};
            let kpi = d.kpi || {};

            $("#total-target").text(money(kpi.target));
            $("#total-achieved").text(money(kpi.achieved));
            $("#total-gap").text(money(kpi.gap));
            $("#total-achievement").text(pct(kpi.achievement));

            render_category_table(d.category_summary || []);
            render_area_table(d.area_summary || []);
            render_gap_table(d.area_summary || []);
            render_charts(d.category_summary || [], d.area_summary || []);
        },
        error: function(err) {
            frappe.msgprint("Dashboard data could not be loaded. Please check server error log.");
            console.error(err);
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
                    <td>${r.category || ""}</td>
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
                    <td>${r.area || ""}</td>
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
        rows = rows.slice().sort((a, b) => (b.gap || 0) - (a.gap || 0));

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
                    <td>${r.area || ""}</td>
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
        $("#category-chart").empty();
        $("#area-chart").empty();

        if (category_rows.length) {
            new frappe.Chart("#category-chart", {
                title: "Category — Achieved vs Gap",
                data: {
                    labels: category_rows.map(r => r.category),
                    datasets: [
                        { name: "Achieved", values: category_rows.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: category_rows.map(r => Math.max(r.gap || 0, 0)) }
                    ]
                },
                type: "bar",
                height: 300,
                colors: ["#4F81BD", "#C0504D"]
            });
        }

        if (area_rows.length) {
            new frappe.Chart("#area-chart", {
                title: "Area — Achieved vs Gap",
                data: {
                    labels: area_rows.map(r => r.area),
                    datasets: [
                        { name: "Achieved", values: area_rows.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: area_rows.map(r => Math.max(r.gap || 0, 0)) }
                    ]
                },
                type: "bar",
                height: 330,
                colors: ["#4F81BD", "#C0504D"]
            });
        }
    }
};