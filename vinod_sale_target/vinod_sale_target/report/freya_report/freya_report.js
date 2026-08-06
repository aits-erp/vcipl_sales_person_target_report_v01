frappe.query_reports["FREYA REPORT"] = {

    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.sys_defaults.year_start_date,
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.sys_defaults.year_end_date,
            reqd: 1
        },
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "custom_sub_group",
            label: "Sub Group",
            fieldtype: "Data"
        },
        {
            fieldname: "custom_item_type",
            label: "Item Type",
            fieldtype: "Data"
        }
    ],

    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        return value;
    }
};