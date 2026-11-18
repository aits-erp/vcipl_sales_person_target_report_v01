// Copyright (c) 2026, Sukku and contributors
// For license information, please see license.txt


// Copyright (c) 2026, Sukku and contributors
// For license information, please see license.txt

function multi_select_from_sales_person(fieldname) {
    return async function (txt) {
        const rows = await frappe.db.get_list("Sales Person", {
            fields: [fieldname],
            filters: [
                [fieldname, "!=", ""],
                [fieldname, "like", "%" + txt + "%"]
            ],
            group_by: fieldname,
            limit: 50
        });

        return [...new Set(rows.map(r => r[fieldname]).filter(Boolean))]
            .sort()
            .map(v => ({ label: v, value: v }));
    };
}

frappe.query_reports["Customer Group Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            // Same company as the Sales Analytics dashboard
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company")
        },
        {
            fieldname: "view_type",
            label: "View Type",
            fieldtype: "Select",
            options: [
                "TSO Summary",
                "Customer Group Summary",
                "Region Summary",
                "North Detail",
                "South Detail",
                "East Detail",
                "Mumbai AH Detail",
                "ROM Detail",
                "MPCG Detail",
                "Gujarat Detail"
            ],
            default: "TSO Summary"
        },
        {
            fieldname: "sales_person",
            label: "TSO",
            fieldtype: "Link",
            options: "Sales Person"
        },
        {
            fieldname: "parent_sales_person",
            label: "Head Sales Person",
            fieldtype: "Link",
            options: "Sales Person"
        },
        {
            fieldname: "custom_region",
            label: "Region",
            fieldtype: "MultiSelectList",
            get_data: multi_select_from_sales_person("custom_region")
        },
        {
            fieldname: "custom_territory",
            label: "Territory Code",
            fieldtype: "MultiSelectList",
            get_data: multi_select_from_sales_person("custom_territory")
        },
        {
            fieldname: "custom_head_sales_code",
            label: "Head Sales Code",
            fieldtype: "MultiSelectList",
            get_data: multi_select_from_sales_person("custom_head_sales_code")
        },
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            // No default: blank = ALL customer groups
            fieldname: "customer_group",
            label: "Customer Group",
            fieldtype: "Link",
            options: "Customer Group"
        },
        {
            // No default: blank = ALL categories (+ "Unmapped" for items without a Main Group)
            fieldname: "custom_main_group",
            label: "Category",
            fieldtype: "MultiSelectList",
            get_data: async function (txt) {
                const rows = await frappe.db.get_list("Item", {
                    fields: ["custom_main_group"],
                    filters: [
                        ["custom_main_group", "!=", ""],
                        ["custom_main_group", "like", "%" + txt + "%"]
                    ],
                    group_by: "custom_main_group",
                    limit: 100
                });

                const values = [...new Set(rows.map(r => r.custom_main_group).filter(Boolean))].sort();
                if ("unmapped".includes((txt || "").toLowerCase())) {
                    values.push("Unmapped");
                }
                return values.map(v => ({ label: v, value: v }));
            }
        },
        {
            fieldname: "show_item_details",
            label: "Include Item Code & Item Name",
            fieldtype: "Check",
            default: 0
        },
        {
            // When checked, "Download MIS Excel" collapses every row sharing the
            // same Customer + TSO + Customer Group into a single summed row.
            fieldname: "party_wise_total",
            label: "Total (Party-wise Grouped Excel)",
            fieldtype: "Check",
            default: 1
        }
    ],

    onload: function (report) {
        report.page.add_inner_button("Download MIS Excel", function () {
            let filters = report.get_values();
            let query = new URLSearchParams(filters).toString();

            window.open(
                "/api/method/vinod_sale_target.vinod_sale_target.report.customer_group_report.customer_group_report.download_mis_excel?"
                + query
            );
        });
    }
};