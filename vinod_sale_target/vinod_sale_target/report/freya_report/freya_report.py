# Copyright (c) 2026, Sukku and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe.utils import flt
import json


def execute(filters=None):

    filters = frappe._dict(filters or {})

    data, customers = get_pivot_data(filters)

    columns = get_columns(customers)

    return columns, data


def get_columns(customers):

    columns = [
        {"label":"Item Code","fieldname":"item_code","width":150},
        {"label":"Item Name","fieldname":"item_name","width":180},
        {"label":"Item Group","fieldname":"item_group","width":180},
        {"label":"Main Group","fieldname":"custom_main_group","width":180},
        {"label":"Sub Group","fieldname":"custom_sub_group","width":180},
    ]

    for customer in customers:

        columns.append({
            "label":customer,
            "fieldname":frappe.scrub(customer),
            "fieldtype":"Float",
            "precision":2,
            "width":140
        })

    columns.append({
        "fieldname":"popup_data",
        "hidden":1
    })

    columns.append({
        "fieldname":"idx",
        "hidden":1
    })

    return columns


def get_pivot_data(filters):

    conditions=""

    values={
        "from_date":filters.from_date,
        "to_date":filters.to_date
    }

    if filters.customer:
        conditions+=" AND si.customer=%(customer)s"
        values["customer"]=filters.customer

    if filters.item_group:
        conditions+=" AND i.item_group=%(item_group)s"
        values["item_group"]=filters.item_group

    if filters.custom_sub_group:
        conditions+=" AND i.custom_sub_group=%(custom_sub_group)s"
        values["custom_sub_group"]=filters.custom_sub_group

    if filters.custom_item_type:
        conditions+=" AND i.custom_item_type=%(custom_item_type)s"
        values["custom_item_type"]=filters.custom_item_type

    if filters.parent_sales_person:
        conditions+=" AND sp.parent_sales_person=%(parent_sales_person)s"
        values["parent_sales_person"]=filters.parent_sales_person

    raw_data=frappe.db.sql(f"""
        SELECT

            sii.item_code,
            sii.item_name,

            i.item_group,
            i.custom_main_group,
            i.custom_sub_group,

            c.customer_name,

            sii.rate,
            sii.base_net_amount as amount

        FROM `tabSales Invoice` si

        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent=si.name

        INNER JOIN `tabItem` i
            ON i.name=sii.item_code

        INNER JOIN `tabCustomer` c
            ON c.name=si.customer

        LEFT JOIN `tabSales Team` st
            ON st.parent=si.name
            AND st.parenttype='Sales Invoice'

        LEFT JOIN `tabSales Person` sp
            ON sp.name=st.sales_person

        WHERE

            si.docstatus=1

            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s

            AND i.custom_main_group='Freya'

            {conditions}

    """,values,as_dict=True)

    customers=sorted({d.customer_name for d in raw_data})

    result={}

    for row in raw_data:

        key=f"{row.item_code}::{row.item_name}::{row.item_group}::{row.custom_main_group}::{row.custom_sub_group}"

        cust=frappe.scrub(row.customer_name)

        if key not in result:

            result[key]={

                "item_code":row.item_code,
                "item_name":row.item_name,
                "item_group":row.item_group,
                "custom_main_group":row.custom_main_group,
                "custom_sub_group":row.custom_sub_group,
                "popup_data":{}

            }

            for c in customers:

                sc=frappe.scrub(c)

                result[key][sc]=0

                result[key]["popup_data"][sc]={}

        result[key][cust]=flt(row.rate)

        items=result[key]["popup_data"][cust]

        if row.item_name not in items:

            items[row.item_name]={

                "item_name":row.item_name,
                "rate":0,
                "amount":0

            }

        items[row.item_name]["rate"]=flt(row.rate)
        items[row.item_name]["amount"]+=flt(row.amount)

    data=[]

    for record in result.values():

        for cust in record["popup_data"]:

            lst=list(record["popup_data"][cust].values())

            avg_rate=0

            if lst:
                avg_rate=sum(i["rate"] for i in lst)/len(lst)

            total_amount=sum(i["amount"] for i in lst)

            lst.append({

                "item_name":"Total",
                "rate":round(avg_rate,2),
                "amount":total_amount

            })

            record["popup_data"][cust]=lst

        record["popup_data"]=json.dumps(record["popup_data"])

        data.append(record)

    for i,row in enumerate(data,1):
        row["idx"]=i

    return data,customers