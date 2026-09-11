// frappe.pages["sales-mis-dashboard"].on_page_load = function(wrapper) {
//     let page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: "Vinod Cookware — Sales MIS Dashboard",
//         single_column: true
//     });

//     // --------------------------------------------------------------
//     // Indian Financial Year quarter helper
//     // Q1: Apr-Jun | Q2: Jul-Sep | Q3: Oct-Dec | Q4: Jan-Mar
//     // --------------------------------------------------------------
//     function get_fy_quarter_dates(quarter, fy_start_year) {
//         // fy_start_year = the "April" year of the FY (e.g. 2026 for FY2026-27)
//         let ranges = {
//             1: { start_month: 4, end_month: 6, year: fy_start_year },
//             2: { start_month: 7, end_month: 9, year: fy_start_year },
//             3: { start_month: 10, end_month: 12, year: fy_start_year },
//             4: { start_month: 1, end_month: 3, year: fy_start_year + 1 }
//         };

//         let r = ranges[quarter];
//         let start = new Date(r.year, r.start_month - 1, 1);
//         let end = new Date(r.year, r.end_month, 0); // last day of end_month

//         return { from_date: fmt_date(start), to_date: fmt_date(end) };
//     }

//     function fmt_date(d) {
//         let m = ("0" + (d.getMonth() + 1)).slice(-2);
//         let dd = ("0" + d.getDate()).slice(-2);
//         return d.getFullYear() + "-" + m + "-" + dd;
//     }

//     function get_current_fy_quarter() {
//         let today = new Date();
//         let month = today.getMonth() + 1;
//         let year = today.getFullYear();

//         let quarter, fy_start_year;

//         if (month >= 4 && month <= 6) {
//             quarter = 1; fy_start_year = year;
//         } else if (month >= 7 && month <= 9) {
//             quarter = 2; fy_start_year = year;
//         } else if (month >= 10 && month <= 12) {
//             quarter = 3; fy_start_year = year;
//         } else {
//             quarter = 4; fy_start_year = year - 1;
//         }

//         return { quarter: quarter, fy_start_year: fy_start_year };
//     }

//     function quarter_label(quarter, fy_start_year) {
//         let fy_end_year = fy_start_year + 1;
//         return "Q" + quarter + " (FY " + fy_start_year + "-" + String(fy_end_year).slice(-2) + ")";
//     }

//     // --------------------------------------------------------------
//     // Current selection state — defaults to the live quarter
//     // --------------------------------------------------------------
//     let current = get_current_fy_quarter();
//     let selected_quarter = current.quarter;
//     let selected_fy_start_year = current.fy_start_year;

//     let dates = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
//     let from_date = dates.from_date;
//     let to_date = dates.to_date;

//     // Build a list of selectable FYs: several years back to several years ahead.
//     // This is calculated from today's date every time the page loads, so the
//     // window itself shifts forward automatically each year — no manual update
//     // needed as years pass, as long as this range is generous enough.
//     let this_calendar_year = new Date().getFullYear();
//     let fy_options = [];
//     for (let y = this_calendar_year - 5; y <= this_calendar_year + 5; y++) {
//         fy_options.push(y);
//     }

//     $(page.body).html(`
//         <style>
//             .mis-wrap {
//                 padding: 18px;
//                 background: #f5f7fb;
//             }

//             .mis-header {
//                 background: linear-gradient(135deg, #064e3b, #0f766e);
//                 color: white;
//                 padding: 18px 22px;
//                 border-radius: 12px;
//                 font-size: 22px;
//                 font-weight: 800;
//                 margin-bottom: 14px;
//                 box-shadow: 0 6px 18px rgba(0,0,0,.12);
//             }

//             .mis-subtitle {
//                 font-size: 13px;
//                 font-weight: 400;
//                 opacity: .9;
//                 margin-top: 5px;
//             }

//             .mis-quarter-bar {
//                 background: white;
//                 border-radius: 12px;
//                 padding: 12px 16px;
//                 box-shadow: 0 4px 14px rgba(0,0,0,.08);
//                 margin-bottom: 18px;
//                 display: flex;
//                 align-items: center;
//                 gap: 14px;
//                 flex-wrap: wrap;
//             }

//             .mis-quarter-bar .quarter-current-label {
//                 font-weight: 800;
//                 color: #0b3d5c;
//                 font-size: 14px;
//                 margin-right: 6px;
//             }

//             .mis-quarter-bar select {
//                 padding: 6px 10px;
//                 border-radius: 8px;
//                 border: 1px solid #cbd5e1;
//                 font-weight: 600;
//                 color: #1e293b;
//             }

//             .quarter-btns {
//                 display: flex;
//                 gap: 8px;
//             }

//             .quarter-btn {
//                 padding: 7px 16px;
//                 border-radius: 8px;
//                 border: 1px solid #0f766e;
//                 background: white;
//                 color: #0f766e;
//                 font-weight: 700;
//                 cursor: pointer;
//                 font-size: 13px;
//                 transition: all .15s ease;
//             }

//             .quarter-btn:hover {
//                 background: #e6f4f1;
//             }

//             .quarter-btn.active {
//                 background: #0f766e;
//                 color: white;
//             }

//             .quarter-range-label {
//                 font-size: 12px;
//                 color: #64748b;
//                 font-weight: 600;
//                 margin-left: auto;
//             }

//             .mis-section-title {
//                 font-size: 16px;
//                 font-weight: 800;
//                 color: #0b3d5c;
//                 margin: 18px 0 10px;
//             }

//             .mis-btn-grid {
//                 display: grid;
//                 grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
//                 gap: 12px;
//                 margin-bottom: 18px;
//             }

//             .mis-btn {
//                 padding: 15px 14px;
//                 border-radius: 12px;
//                 color: white;
//                 font-weight: 800;
//                 cursor: pointer;
//                 text-align: center;
//                 box-shadow: 0 6px 15px rgba(0,0,0,.15);
//                 transition: all .2s ease;
//                 min-height: 70px;
//                 display: flex;
//                 align-items: center;
//                 justify-content: center;
//                 flex-direction: column;
//             }

//             .mis-btn:hover {
//                 transform: translateY(-3px);
//                 box-shadow: 0 10px 25px rgba(0,0,0,.22);
//             }

//             .mis-btn small {
//                 font-size: 11px;
//                 opacity: .9;
//                 margin-top: 4px;
//                 font-weight: 600;
//             }

//             .green { background: linear-gradient(135deg, #047857, #10b981); }
//             .blue { background: linear-gradient(135deg, #1d4ed8, #2563eb); }
//             .purple { background: linear-gradient(135deg, #6b21a8, #9333ea); }
//             .orange { background: linear-gradient(135deg, #c2410c, #f97316); }
//             .red { background: linear-gradient(135deg, #991b1b, #dc2626); }
//             .teal { background: linear-gradient(135deg, #0f766e, #14b8a6); }
//             .dark { background: linear-gradient(135deg, #1f2937, #4b5563); }
//             .pink { background: linear-gradient(135deg, #be185d, #ec4899); }
//             .yellow { background: linear-gradient(135deg, #a16207, #eab308); }
//             .black { background: linear-gradient(135deg, #111827, #0f766e); }

//             .mis-kpis {
//                 display: grid;
//                 grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
//                 gap: 14px;
//                 margin-bottom: 18px;
//             }

//             .kpi-card {
//                 background: white;
//                 border-radius: 12px;
//                 padding: 16px;
//                 box-shadow: 0 4px 14px rgba(0,0,0,.08);
//                 border-left: 6px solid #0f766e;
//             }

//             .kpi-label {
//                 font-size: 13px;
//                 color: #64748b;
//                 font-weight: 600;
//             }

//             .kpi-value {
//                 font-size: 23px;
//                 font-weight: 800;
//                 margin-top: 6px;
//                 color: #1e293b;
//             }

//             .mis-grid {
//                 display: grid;
//                 grid-template-columns: 42% 58%;
//                 gap: 14px;
//             }

//             .panel {
//                 background: white;
//                 border-radius: 12px;
//                 padding: 14px;
//                 box-shadow: 0 4px 14px rgba(0,0,0,.08);
//                 margin-bottom: 14px;
//             }

//             .panel-title {
//                 font-weight: 800;
//                 color: #0b3d5c;
//                 margin-bottom: 10px;
//                 font-size: 14px;
//             }

//             table.mis-table {
//                 width: 100%;
//                 border-collapse: collapse;
//                 font-size: 12px;
//             }

//             .mis-table th {
//                 background: #0b3d5c;
//                 color: white;
//                 padding: 7px;
//                 border: 1px solid #ddd;
//                 text-align: center;
//             }

//             .mis-table td {
//                 padding: 6px;
//                 border: 1px solid #ddd;
//             }

//             .target { background: #fff2cc; text-align: right; }
//             .achieved { background: #ddebf7; text-align: right; }
//             .gap { background: #fce4d6; text-align: right; }
//             .percent { background: #e2f0d9; text-align: right; font-weight: 800; }

//             @media(max-width: 900px) {
//                 .mis-grid {
//                     grid-template-columns: 1fr;
//                 }
//                 .quarter-range-label {
//                     margin-left: 0;
//                 }
//             }
//         </style>

//         <div class="mis-wrap">
//             <div class="mis-header">
//                 Vinod Cookware — <span id="header-quarter-label"></span> Performance Dashboard
//                 <div class="mis-subtitle">
//                     One-click MIS dashboard with all worksheet sections and full Excel download.
//                 </div>
//             </div>

//             <div class="mis-quarter-bar">
//                 <span class="quarter-current-label">Financial Year</span>
//                 <select id="fy-select"></select>

//                 <div class="quarter-btns" id="quarter-btns">
//                     <div class="quarter-btn" data-q="1">Q1 (Apr-Jun)</div>
//                     <div class="quarter-btn" data-q="2">Q2 (Jul-Sep)</div>
//                     <div class="quarter-btn" data-q="3">Q3 (Oct-Dec)</div>
//                     <div class="quarter-btn" data-q="4">Q4 (Jan-Mar)</div>
//                 </div>

//                 <span class="quarter-range-label" id="quarter-range-label"></span>
//             </div>

//             <div class="mis-section-title">Worksheet Reports</div>
//             <div class="mis-btn-grid">

//                 <div class="mis-btn green" data-view="TSO Summary">
//                     TSO Summary
//                     <small>Distributor-wise target vs achievement</small>
//                 </div>

//                 <div class="mis-btn blue" data-view="Region Summary">
//                     Region Summary
//                     <small>Area-wise consolidated report</small>
//                 </div>

//                 <div class="mis-btn purple" id="charts-section">
//                     Charts
//                     <small>Category and area performance charts</small>
//                 </div>

//                 <div class="mis-btn pink" data-view="Mumbai AH Detail">
//                     Mumbai AH Details
//                     <small>TSOMUM1 to TSOMUM5</small>
//                 </div>

//                 <div class="mis-btn orange" data-view="ROM Detail">
//                     ROM Details
//                     <small>HSROM</small>
//                 </div>

//                 <div class="mis-btn yellow" data-view="MPCG Detail">
//                     MPCG Details
//                     <small>HSMPCG</small>
//                 </div>

//                 <div class="mis-btn red" data-view="Gujarat Detail">
//                     Gujarat Details
//                     <small>TSOSRT1</small>
//                 </div>

//                 <div class="mis-btn blue" data-view="North Detail">
//                     North TSO Details
//                     <small>North region detail</small>
//                 </div>

//                 <div class="mis-btn teal" data-view="East Detail">
//                     East TSO Details
//                     <small>East region detail</small>
//                 </div>

//                 <div class="mis-btn green" data-view="South Detail">
//                     South TSO Details
//                     <small>South region detail</small>
//                 </div>
                
                
            

//                 <div class="mis-btn black" id="download-full-excel">
//                     Download Full MIS Excel
//                     <small>Download all worksheet reports</small>
//                 </div>

//             </div>

//             <div class="mis-kpis">
//                 <div class="kpi-card">
//                     <div class="kpi-label">Total Target</div>
//                     <div class="kpi-value" id="total-target">0</div>
//                 </div>
//                 <div class="kpi-card">
//                     <div class="kpi-label">Total Achieved</div>
//                     <div class="kpi-value" id="total-achieved">0</div>
//                 </div>
//                 <div class="kpi-card">
//                     <div class="kpi-label">Not Achieved</div>
//                     <div class="kpi-value" id="total-gap">0</div>
//                 </div>
//                 <div class="kpi-card">
//                     <div class="kpi-label">Achievement %</div>
//                     <div class="kpi-value" id="total-achievement">0%</div>
//                 </div>
//             </div>

//             <div class="mis-grid">
//                 <div>
//                     <div class="panel">
//                         <div class="panel-title">Chart 1 — Category-wise: Achieved vs Gap</div>
//                         <table class="mis-table" id="category-table"></table>
//                     </div>

                    

//                    <!--
//                    <div class="panel">
//                         <div class="panel-title">Chart 2 — Area-wise: Achieved vs Gap</div>
//                         <table class="mis-table" id="area-table"></table>
//                     </div>
//                     -->

//                     <div class="panel">
//                         <div class="panel-title">Gap Summary — Total Not Achieved by Area</div>
//                         <table class="mis-table" id="gap-table"></table>
//                     </div>
//                 </div>

//                 <div>
//                     <div class="panel">
//                         <div id="category-chart"></div>
//                     </div>

//                     <div class="panel">
//                         <div id="area-chart"></div>
//                     </div>
//                 </div>
//             </div>
//         </div>
//     `);

//     function money(v) {
//         return format_currency(v || 0, "INR");
//     }

//     function pct(v) {
//         return (v || 0).toFixed(1) + "%";
//     }

//     function open_report(view_type) {
//         frappe.set_route("query-report", "TEST REPORT", {
//             from_date: from_date,
//             to_date: to_date,
//             customer_group: "Debtors Distributors",
//             view_type: view_type
//         });
//     }

//     $(page.body).find(".mis-btn[data-view]").on("click", function() {
//         open_report($(this).data("view"));
//     });

//     $(page.body).find("#charts-section").on("click", function() {
//         $("html, body").animate({
//             scrollTop: $("#category-chart").offset().top - 120
//         }, 400);
//     });

//     $(page.body).find("#download-full-excel").on("click", function() {
//         let filters = {
//             from_date: from_date,
//             to_date: to_date,
//             customer_group: "Debtors Distributors",
//             view_type: "TSO Summary"
//         };

//         let query = new URLSearchParams(filters).toString();

//         window.open(
//             "/api/method/vinod_sale_target.vinod_sale_target.report.test_report.test_report.download_mis_excel?"
//             + query
//         );
//     });

//     // --------------------------------------------------------------
//     // Quarter switcher wiring
//     // --------------------------------------------------------------
//     let $fy_select = $(page.body).find("#fy-select");

//     fy_options.forEach(y => {
//         $fy_select.append(
//             `<option value="${y}">FY ${y}-${String(y + 1).slice(-2)}</option>`
//         );
//     });
//     $fy_select.val(selected_fy_start_year);

//     function update_quarter_ui() {
//         $(page.body).find(".quarter-btn").removeClass("active");
//         $(page.body).find(`.quarter-btn[data-q="${selected_quarter}"]`).addClass("active");

//         let label = quarter_label(selected_quarter, selected_fy_start_year);
//         $("#header-quarter-label").text(label);
//         $("#quarter-range-label").text(
//             frappe.datetime.str_to_user(from_date) + "  to  " + frappe.datetime.str_to_user(to_date)
//         );
//     }

//     function apply_quarter_change() {
//         let dates = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
//         from_date = dates.from_date;
//         to_date = dates.to_date;
//         update_quarter_ui();
//         load_dashboard_data();
//     }

//     $(page.body).find(".quarter-btn").on("click", function() {
//         selected_quarter = parseInt($(this).data("q"));
//         apply_quarter_change();
//     });

//     $fy_select.on("change", function() {
//         selected_fy_start_year = parseInt($(this).val());
//         apply_quarter_change();
//     });

//     update_quarter_ui();

//     // --------------------------------------------------------------
//     // Data loading
//     // --------------------------------------------------------------
//     function load_dashboard_data() {
//         frappe.call({
//             method: "vinod_sale_target.vinod_sale_target.report.test_report.test_report.get_mis_dashboard_data",
//             args: {
//                 from_date: from_date,
//                 to_date: to_date
//             },
//             callback: function(r) {
//                 let d = r.message || {};
//                 let kpi = d.kpi || {};

//                 $("#total-target").text(money(kpi.target));
//                 $("#total-achieved").text(money(kpi.achieved));
//                 $("#total-gap").text(money(kpi.gap));
//                 $("#total-achievement").text(pct(kpi.achievement));

//                 render_category_table(d.category_summary || []);
//                 render_area_table(d.area_summary || []);
//                 render_gap_table(d.area_summary || []);
//                 render_charts(d.category_summary || [], d.area_summary || []);
//             },
//             error: function(err) {
//                 frappe.msgprint("Dashboard data could not be loaded. Please check server error log.");
//                 console.error(err);
//             }
//         });
//     }

//     load_dashboard_data();

//     function render_category_table(rows) {
//         let html = `
//             <tr>
//                 <th>Category</th>
//                 <th>Target</th>
//                 <th>Achieved</th>
//                 <th>Gap</th>
//                 <th>%Ach</th>
//             </tr>
//         `;

//         rows.forEach(r => {
//             html += `
//                 <tr>
//                     <td>${r.category || ""}</td>
//                     <td class="target">${money(r.target)}</td>
//                     <td class="achieved">${money(r.achieved)}</td>
//                     <td class="gap">${money(r.gap)}</td>
//                     <td class="percent">${pct(r.achievement)}</td>
//                 </tr>
//             `;
//         });

//         $("#category-table").html(html);
//     }

//     function render_area_table(rows) {
//         let html = `
//             <tr>
//                 <th>Area</th>
//                 <th>Target</th>
//                 <th>Achieved</th>
//                 <th>Gap</th>
//                 <th>%Ach</th>
//             </tr>
//         `;

//         rows.forEach(r => {
//             html += `
//                 <tr>
//                     <td>${r.area || ""}</td>
//                     <td class="target">${money(r.target)}</td>
//                     <td class="achieved">${money(r.achieved)}</td>
//                     <td class="gap">${money(r.gap)}</td>
//                     <td class="percent">${pct(r.achievement)}</td>
//                 </tr>
//             `;
//         });

//         $("#area-table").html(html);
//     }

//     function render_gap_table(rows) {
//         rows = rows.slice().sort((a, b) => (b.gap || 0) - (a.gap || 0));

//         let html = `
//             <tr>
//                 <th>Area</th>
//                 <th>Target</th>
//                 <th>Achieved</th>
//                 <th>Gap</th>
//                 <th>%Ach</th>
//             </tr>
//         `;

//         rows.forEach(r => {
//             html += `
//                 <tr>
//                     <td>${r.area || ""}</td>
//                     <td class="target">${money(r.target)}</td>
//                     <td class="achieved">${money(r.achieved)}</td>
//                     <td class="gap">${money(r.gap)}</td>
//                     <td class="percent">${pct(r.achievement)}</td>
//                 </tr>
//             `;
//         });

//         $("#gap-table").html(html);
//     }

//     function render_charts(category_rows, area_rows) {
//         $("#category-chart").empty();
//         $("#area-chart").empty();

//         if (category_rows.length) {
//             new frappe.Chart("#category-chart", {
//                 title: "Category — Achieved vs Gap",
//                 data: {
//                     labels: category_rows.map(r => r.category),
//                     datasets: [
//                         { name: "Achieved", values: category_rows.map(r => r.achieved || 0) },
//                         { name: "Not Achieved", values: category_rows.map(r => Math.max(r.gap || 0, 0)) }
//                     ]
//                 },
//                 type: "bar",
//                 height: 300,
//                 colors: ["#4F81BD", "#C0504D"]
//             });
//         }

//         if (area_rows.length) {
//             new frappe.Chart("#area-chart", {
//                 title: "Area — Achieved vs Gap",
//                 data: {
//                     labels: area_rows.map(r => r.area),
//                     datasets: [
//                         { name: "Achieved", values: area_rows.map(r => r.achieved || 0) },
//                         { name: "Not Achieved", values: area_rows.map(r => Math.max(r.gap || 0, 0)) }
//                     ]
//                 },
//                 type: "bar",
//                 height: 330,
//                 colors: ["#4F81BD", "#C0504D"]
//             });
//         }
//     }
// };




frappe.pages["sales-mis-dashboard"].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vinod Cookware — Sales MIS Dashboard",
        single_column: true
    });

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

    function fmt_date(d) {
        let m = ("0" + (d.getMonth() + 1)).slice(-2);
        let dd = ("0" + d.getDate()).slice(-2);
        return d.getFullYear() + "-" + m + "-" + dd;
    }

    function get_current_fy_quarter() {
        let today = new Date();
        let month = today.getMonth() + 1;
        let year = today.getFullYear();

        let quarter, fy_start_year;

        if (month >= 4 && month <= 6) {
            quarter = 1; fy_start_year = year;
        } else if (month >= 7 && month <= 9) {
            quarter = 2; fy_start_year = year;
        } else if (month >= 10 && month <= 12) {
            quarter = 3; fy_start_year = year;
        } else {
            quarter = 4; fy_start_year = year - 1;
        }

        return { quarter: quarter, fy_start_year: fy_start_year };
    }

    function quarter_label(quarter, fy_start_year) {
        let fy_end_year = fy_start_year + 1;
        return "Q" + quarter + " (FY " + fy_start_year + "-" + String(fy_end_year).slice(-2) + ")";
    }

    let current = get_current_fy_quarter();
    let selected_quarter = current.quarter;
    let selected_fy_start_year = current.fy_start_year;

    let dates = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
    let from_date = dates.from_date;
    let to_date = dates.to_date;

    let this_calendar_year = new Date().getFullYear();
    let fy_options = [];
    for (let y = this_calendar_year - 5; y <= this_calendar_year + 5; y++) {
        fy_options.push(y);
    }

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
                margin-bottom: 14px;
                box-shadow: 0 6px 18px rgba(0,0,0,.12);
            }

            .mis-subtitle {
                font-size: 13px;
                font-weight: 400;
                opacity: .9;
                margin-top: 5px;
            }

            .mis-quarter-bar {
                background: white;
                border-radius: 12px;
                padding: 12px 16px;
                box-shadow: 0 4px 14px rgba(0,0,0,.08);
                margin-bottom: 18px;
                display: flex;
                align-items: center;
                gap: 14px;
                flex-wrap: wrap;
            }

            .mis-quarter-bar .quarter-current-label {
                font-weight: 800;
                color: #0b3d5c;
                font-size: 14px;
                margin-right: 6px;
            }

            .mis-quarter-bar select {
                padding: 6px 10px;
                border-radius: 8px;
                border: 1px solid #cbd5e1;
                font-weight: 600;
                color: #1e293b;
            }

            .quarter-btns {
                display: flex;
                gap: 8px;
            }

            .quarter-btn {
                padding: 7px 16px;
                border-radius: 8px;
                border: 1px solid #0f766e;
                background: white;
                color: #0f766e;
                font-weight: 700;
                cursor: pointer;
                font-size: 13px;
                transition: all .15s ease;
            }

            .quarter-btn:hover {
                background: #e6f4f1;
            }

            .quarter-btn.active {
                background: #0f766e;
                color: white;
            }

            .custom-range-bar {
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
                padding: 10px 16px;
                background: #f0fdf4;
                border-radius: 10px;
                border: 1px solid #bbf7d0;
                margin-top: 4px;
                width: 100%;
            }

            .custom-range-bar label {
                font-weight: 700;
                color: #0b3d5c;
                font-size: 13px;
            }

            .custom-range-bar input[type="date"] {
                padding: 5px 8px;
                border-radius: 8px;
                border: 1px solid #cbd5e1;
                font-weight: 600;
                color: #1e293b;
                font-size: 12px;
            }

            .custom-range-bar button {
                padding: 6px 16px;
                border-radius: 8px;
                background: #0f766e;
                color: white;
                border: none;
                font-weight: 700;
                cursor: pointer;
                font-size: 12px;
                transition: background .15s;
            }

            .custom-range-bar button:hover {
                background: #064e3b;
            }

            .quarter-range-label {
                font-size: 12px;
                color: #64748b;
                font-weight: 600;
                margin-left: auto;
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

            .green  { background: linear-gradient(135deg, #047857, #10b981); }
            .blue   { background: linear-gradient(135deg, #1d4ed8, #2563eb); }
            .purple { background: linear-gradient(135deg, #6b21a8, #9333ea); }
            .orange { background: linear-gradient(135deg, #c2410c, #f97316); }
            .red    { background: linear-gradient(135deg, #991b1b, #dc2626); }
            .teal   { background: linear-gradient(135deg, #0f766e, #14b8a6); }
            .dark   { background: linear-gradient(135deg, #1f2937, #4b5563); }
            .pink   { background: linear-gradient(135deg, #be185d, #ec4899); }
            .yellow { background: linear-gradient(135deg, #a16207, #eab308); }
            .black  { background: linear-gradient(135deg, #111827, #0f766e); }

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

            .target   { background: #fff2cc; text-align: right; }
            .achieved { background: #ddebf7; text-align: right; }
            .gap      { background: #fce4d6; text-align: right; }
            .percent  { background: #e2f0d9; text-align: right; font-weight: 800; }

            .region-cat-filter {
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 10px;
            }

            .region-cat-filter select {
                padding: 5px 10px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
                font-size: 12px;
                font-weight: 600;
                color: #1e293b;
            }

            .region-cat-filter label {
                font-size: 12px;
                font-weight: 700;
                color: #0b3d5c;
            }

            @media(max-width: 900px) {
                .mis-grid { grid-template-columns: 1fr; }
                .quarter-range-label { margin-left: 0; }
            }
        </style>

        <div class="mis-wrap">
            <div class="mis-header">
                Vinod Cookware — <span id="header-quarter-label"></span> Performance Dashboard
                <div class="mis-subtitle">
                    One-click MIS dashboard with all worksheet sections and full Excel download.
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

                <!-- ✅ NEW: Custom date range bar -->
                <div class="custom-range-bar">
                    <label>Custom Range:</label>
                    <input type="date" id="custom-from-date">
                    <span style="font-weight:600;color:#64748b;font-size:12px;">to</span>
                    <input type="date" id="custom-to-date">
                    <button id="apply-custom-range">Apply</button>
                    <span id="custom-range-active-label" style="font-size:11px;color:#0f766e;font-weight:700;display:none;">
                        ✓ Custom range active
                    </span>
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

                <div class="mis-btn blue" data-view="North Detail">
                    North TSO Details
                    <small>North region detail</small>
                </div>

                <div class="mis-btn teal" data-view="East Detail">
                    East TSO Details
                    <small>East region detail</small>
                </div>

                <div class="mis-btn green" data-view="South Detail">
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

                    <!--
                    <div class="panel">
                        <div class="panel-title">Chart 2 — Area-wise: Achieved vs Gap</div>
                        <table class="mis-table" id="area-table"></table>
                    </div>
                    -->

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

                    <!-- ✅ NEW: Region × Category chart panel -->
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

    // --------------------------------------------------------------
    // Quarter switcher wiring
    // --------------------------------------------------------------
    let $fy_select = $(page.body).find("#fy-select");

    fy_options.forEach(y => {
        $fy_select.append(
            `<option value="${y}">FY ${y}-${String(y + 1).slice(-2)}</option>`
        );
    });
    $fy_select.val(selected_fy_start_year);

    function update_quarter_ui() {
        $(page.body).find(".quarter-btn").removeClass("active");
        $(page.body).find(`.quarter-btn[data-q="${selected_quarter}"]`).addClass("active");

        let label = quarter_label(selected_quarter, selected_fy_start_year);
        $("#header-quarter-label").text(label);
        $("#quarter-range-label").text(
            frappe.datetime.str_to_user(from_date) + "  to  " + frappe.datetime.str_to_user(to_date)
        );

        // hide custom-range active label when quarter is selected
        $(page.body).find("#custom-range-active-label").hide();
    }

    function apply_quarter_change() {
        let d = get_fy_quarter_dates(selected_quarter, selected_fy_start_year);
        from_date = d.from_date;
        to_date   = d.to_date;

        // sync date inputs with selected quarter
        $(page.body).find("#custom-from-date").val(from_date);
        $(page.body).find("#custom-to-date").val(to_date);

        update_quarter_ui();
        load_dashboard_data();
    }

    $(page.body).find(".quarter-btn").on("click", function() {
        selected_quarter = parseInt($(this).data("q"));
        apply_quarter_change();
    });

    $fy_select.on("change", function() {
        selected_fy_start_year = parseInt($(this).val());
        apply_quarter_change();
    });

    // ✅ NEW: Custom date range apply
    $(page.body).find("#custom-from-date").val(from_date);
    $(page.body).find("#custom-to-date").val(to_date);

    $(page.body).find("#apply-custom-range").on("click", function() {
        let f = $(page.body).find("#custom-from-date").val();
        let t = $(page.body).find("#custom-to-date").val();

        if (!f || !t) {
            frappe.msgprint("Please select both From and To dates.");
            return;
        }
        if (f > t) {
            frappe.msgprint("From date cannot be after To date.");
            return;
        }

        // deactivate quarter buttons — custom range is now active
        $(page.body).find(".quarter-btn").removeClass("active");
        selected_quarter = null;

        from_date = f;
        to_date   = t;

        $("#header-quarter-label").text("Custom Range");
        $("#quarter-range-label").text(
            frappe.datetime.str_to_user(from_date) + "  to  " + frappe.datetime.str_to_user(to_date)
        );
        $(page.body).find("#custom-range-active-label").show();

        load_dashboard_data();
    });

    update_quarter_ui();

    // --------------------------------------------------------------
    // Data loading
    // --------------------------------------------------------------
    let _last_category_data = [];
    let _last_area_data     = [];

    // ✅ NEW: Region × Category filter change
    $(page.body).find("#region-cat-region").on("change", function() {
        render_region_cat_chart(_last_category_data, _last_area_data);
    });

    function load_dashboard_data() {
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

                _last_category_data = d.category_summary || [];
                _last_area_data     = d.area_summary     || [];

                render_category_table(_last_category_data);
                render_area_table(_last_area_data);
                render_gap_table(_last_area_data);
                render_charts(_last_category_data, _last_area_data);
                render_region_cat_chart(_last_category_data, _last_area_data);
            },
            error: function(err) {
                frappe.msgprint("Dashboard data could not be loaded. Please check server error log.");
                console.error(err);
            }
        });
    }

    load_dashboard_data();

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
                        { name: "Achieved",     values: category_rows.map(r => r.achieved || 0) },
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
                        { name: "Achieved",     values: area_rows.map(r => r.achieved || 0) },
                        { name: "Not Achieved", values: area_rows.map(r => Math.max(r.gap || 0, 0)) }
                    ]
                },
                type: "bar",
                height: 330,
                colors: ["#4F81BD", "#C0504D"]
            });
        }
    }

    // ✅ NEW: Region × Category chart
    function render_region_cat_chart(category_rows, area_rows) {
        let selected_region = $(page.body).find("#region-cat-region").val();

        let labels   = category_rows.map(r => r.category);
        let targets  = category_rows.map(r => r.target   || 0);
        let achieved = category_rows.map(r => r.achieved || 0);
        let gap      = category_rows.map(r => Math.max(r.gap || 0, 0));

        // If a specific region is selected, scale proportionally
        // using that region's share of total achieved & target
        if (selected_region && area_rows.length) {
            let area = area_rows.find(a => a.area === selected_region);
            let total_achieved_all = area_rows.reduce((s, a) => s + (a.achieved || 0), 0);
            let total_target_all   = area_rows.reduce((s, a) => s + (a.target   || 0), 0);

            let ach_ratio = (area && total_achieved_all) ? area.achieved / total_achieved_all : 1;
            let tgt_ratio = (area && total_target_all)   ? area.target   / total_target_all   : 1;

            targets  = category_rows.map(r => (r.target   || 0) * tgt_ratio);
            achieved = category_rows.map(r => (r.achieved || 0) * ach_ratio);
            gap      = targets.map((t, i) => Math.max(t - achieved[i], 0));
        }

        // Render chart
        $("#region-cat-chart").empty();
        if (labels.length) {
            new frappe.Chart("#region-cat-chart", {
                title: selected_region
                    ? `${selected_region} — Category Target vs Achieved`
                    : "All Regions — Category Target vs Achieved",
                data: {
                    labels: labels,
                    datasets: [
                        { name: "Target",       values: targets  },
                        { name: "Achieved",     values: achieved },
                        { name: "Not Achieved", values: gap      }
                    ]
                },
                type: "bar",
                height: 320,
                colors: ["#FFC107", "#4F81BD", "#C0504D"]
            });
        }

        // Render table below chart
        let html = `
            <tr>
                <th>Category</th>
                <th>Target</th>
                <th>Achieved</th>
                <th>Gap</th>
                <th>%Ach</th>
            </tr>
        `;

        category_rows.forEach((r, i) => {
            let t = targets[i];
            let a = achieved[i];
            let g = Math.max(t - a, 0);
            let p = t ? (a / t * 100) : 0;

            html += `
                <tr>
                    <td>${r.category || ""}</td>
                    <td class="target">${money(t)}</td>
                    <td class="achieved">${money(a)}</td>
                    <td class="gap">${money(g)}</td>
                    <td class="percent">${pct(p)}</td>
                </tr>
            `;
        });

        $("#region-cat-table").html(html);
    }

};