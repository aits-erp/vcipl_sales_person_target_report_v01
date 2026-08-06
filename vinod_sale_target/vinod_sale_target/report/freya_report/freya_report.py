import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})

    data, customers = get_pivot_data(filters)
    columns = get_columns(customers)

    return columns, data


# ---------------------------------------------------------
# COLUMNS
# ---------------------------------------------------------
def get_columns(customers):

    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Data", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
    ]

    # ONE COLUMN PER CUSTOMER -> AMOUNT
    for customer in customers:
        columns.append({
            "label": customer,
            "fieldname": frappe.scrub(customer),
            "fieldtype": "Currency",
            "width": 150
        })

    return columns


# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------
def get_pivot_data(filters):

    conditions = ""
    values = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        # LOCKED VALUES - Freya report only ever looks at this group/main group
        "item_group": "Freya",
        "custom_main_group": "Freya Cast Iron",
    }

    if filters.customer:
        conditions += " AND si.customer = %(customer)s"
        values["customer"] = filters.customer

    if filters.custom_sub_group:
        conditions += " AND i.custom_sub_group = %(custom_sub_group)s"
        values["custom_sub_group"] = filters.custom_sub_group

    if filters.custom_item_type:
        conditions += " AND i.custom_item_type = %(custom_item_type)s"
        values["custom_item_type"] = filters.custom_item_type

    if filters.parent_sales_person:
        conditions += " AND sp.parent_sales_person = %(parent_sales_person)s"
        values["parent_sales_person"] = filters.parent_sales_person

    raw_data = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            sii.item_name,
            c.customer_name,
            sii.qty,
            sii.base_net_amount AS amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        JOIN `tabItem` i ON i.name = sii.item_code
        JOIN `tabCustomer` c ON c.name = si.customer
        LEFT JOIN `tabSales Team` st
            ON st.parent = si.name
            AND st.parenttype = 'Sales Invoice'
        LEFT JOIN `tabSales Person` sp
            ON sp.name = st.sales_person
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND i.item_group = %(item_group)s
          AND i.custom_main_group = %(custom_main_group)s
          {conditions}
        """,
        values,
        as_dict=True
    )

    # ---------------------------------------------
    # UNIQUE CUSTOMERS (columns)
    # ---------------------------------------------
    customers = sorted({row.customer_name for row in raw_data})

    result = {}

    # ---------------------------------------------
    # BUILD PIVOT: ITEM x CUSTOMER -> AMOUNT
    # ---------------------------------------------
    for row in raw_data:

        item_code = row.item_code or "Undefined"
        item_name = row.item_name or "Undefined"
        customer = row.customer_name

        key = f"{item_code}::{item_name}"
        cust_field = frappe.scrub(customer)

        if key not in result:
            result[key] = {
                "item_code": item_code,
                "item_name": item_name,
            }
            for c in customers:
                result[key][frappe.scrub(c)] = 0

        result[key][cust_field] += flt(row.amount)

    data = sorted(result.values(), key=lambda r: r["item_name"])

    return data, customers