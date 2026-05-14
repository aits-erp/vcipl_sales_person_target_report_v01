# import frappe
# from frappe.utils import flt, getdate
# from frappe import _

# MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
#           "Jul","Aug","Sep","Oct","Nov","Dec"]

# def execute(filters=None):
#     filters = frappe._dict(filters or {})
    
#     # Validate dates
#     if filters.get("from_date") and filters.get("to_date"):
#         if getdate(filters.from_date) > getdate(filters.to_date):
#             frappe.throw(_("From Date must be before To Date"))
    
#     categories = get_categories(filters)
#     columns = get_columns(categories, filters)
#     data = get_data(filters, categories)
    
#     chart = get_chart_data(data, categories)
#     summary = get_summary(data, categories)
    
#     return columns, data, None, chart, summary


# def get_categories(filters):
#     if filters.get("custom_main_group"):
#         if isinstance(filters.custom_main_group, list):
#             return filters.custom_main_group
#         return [filters.custom_main_group]
    
#     conditions = ""
#     values = {}
    
#     if filters.get("from_date"):
#         conditions += " AND si.posting_date >= %(from_date)s"
#         values["from_date"] = filters.get("from_date")
    
#     if filters.get("to_date"):
#         conditions += " AND si.posting_date <= %(to_date)s"
#         values["to_date"] = filters.get("to_date")
    
#     categories = frappe.db.sql("""
#         SELECT DISTINCT i.custom_main_group
#         FROM `tabSales Invoice` si
#         INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
#         INNER JOIN `tabItem` i ON i.name = sii.item_code
#         WHERE si.docstatus = 1
#         AND i.custom_main_group IS NOT NULL
#         AND i.custom_main_group != ''
#         {conditions}
#         ORDER BY i.custom_main_group
#     """.format(conditions=conditions), values)
    
#     return [c[0] for c in categories if c[0]]


# def get_columns(categories, filters=None):
#     columns = []

#     if filters and filters.get("show_item_details"):
#         columns.extend([
#             {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
#             {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200}
#         ])

#     columns.extend([
#         {"label": _("Month"),              "fieldname": "month",               "fieldtype": "Data",     "width": 100, "align": "center"},
#         {"label": _("TSO"),                "fieldname": "tso_name",            "fieldtype": "Link",     "options": "Sales Person", "width": 200},
#         {"label": _("Customer Name"),      "fieldname": "customer_name",       "fieldtype": "Data",     "width": 200},
#         {"label": _("Region"),             "fieldname": "custom_region",       "fieldtype": "Data",     "width": 150},
#         {"label": _("Head Sales Person"),  "fieldname": "parent_sales_person", "fieldtype": "Link",     "options": "Sales Person", "width": 200},
#         {"label": _("Total Achieved"),     "fieldname": "total_achieved",      "fieldtype": "Currency", "width": 150},
#         {"label": _("Total Target"),       "fieldname": "total_target",        "fieldtype": "Currency", "width": 150}
#     ])

#     for cat in categories:
#         safe = cat.replace(" ", "_").replace("-", "_")
#         columns.append({"label": _(f"{cat} (Target)"),   "fieldname": f"{safe}_target",   "fieldtype": "Currency"})
#         columns.append({"label": _(f"{cat} (Achieved)"), "fieldname": f"{safe}_achieved", "fieldtype": "Currency"})

#     return columns


# # ─────────────────────────────────────────────
# # TARGET CACHE — fetch once per (tso, month, year)
# # ─────────────────────────────────────────────
# _target_cache = {}

# def _load_targets_for_tso(tso_name, month_num, year):
#     """
#     Load all main_group targets for a given TSO + month + year.
#     Tries multiple possible column name combinations to handle
#     different DocType field naming conventions.
#     Returns a dict { main_group: target_amount }
#     """
#     cache_key = (tso_name, month_num, year)
#     if cache_key in _target_cache:
#         return _target_cache[cache_key]

#     result = {}

#     # -------------------------------------------------------------------
#     # Strategy 1: year is on the PARENT table (tabSales Person Target)
#     # Most common pattern — try this first
#     # -------------------------------------------------------------------
#     try:
#         rows = frappe.db.sql("""
#             SELECT
#                 mtd.main_group,
#                 mtd.target_amount
#             FROM `tabMonthly Target Detail` mtd
#             INNER JOIN `tabSales Person Target` spt
#                 ON spt.name = mtd.parent
#             WHERE spt.sales_person = %(tso_name)s
#               AND mtd.month        = %(month_num)s
#               AND spt.year         = %(year)s
#               AND spt.docstatus    = 1
#         """, {
#             "tso_name":  tso_name,
#             "month_num": month_num,
#             "year":      year
#         }, as_dict=1)

#         result = {r.main_group: flt(r.target_amount) for r in rows}
#         _target_cache[cache_key] = result
#         return result

#     except Exception:
#         pass  # Column name mismatch — try next strategy

#     # -------------------------------------------------------------------
#     # Strategy 2: parent uses 'customer' instead of 'sales_person'
#     # -------------------------------------------------------------------
#     try:
#         rows = frappe.db.sql("""
#             SELECT
#                 mtd.main_group,
#                 mtd.target_amount
#             FROM `tabMonthly Target Detail` mtd
#             INNER JOIN `tabSales Person Target` spt
#                 ON spt.name = mtd.parent
#             WHERE spt.customer   = %(tso_name)s
#               AND mtd.month      = %(month_num)s
#               AND spt.year       = %(year)s
#               AND spt.docstatus  = 1
#         """, {
#             "tso_name":  tso_name,
#             "month_num": month_num,
#             "year":      year
#         }, as_dict=1)

#         result = {r.main_group: flt(r.target_amount) for r in rows}
#         _target_cache[cache_key] = result
#         return result

#     except Exception:
#         pass

#     # -------------------------------------------------------------------
#     # Strategy 3: year is on the CHILD table (tabMonthly Target Detail)
#     # with fieldname 'target_year'
#     # -------------------------------------------------------------------
#     try:
#         rows = frappe.db.sql("""
#             SELECT
#                 mtd.main_group,
#                 mtd.target_amount
#             FROM `tabMonthly Target Detail` mtd
#             INNER JOIN `tabSales Person Target` spt
#                 ON spt.name = mtd.parent
#             WHERE spt.sales_person  = %(tso_name)s
#               AND mtd.month         = %(month_num)s
#               AND mtd.target_year   = %(year)s
#               AND spt.docstatus     = 1
#         """, {
#             "tso_name":  tso_name,
#             "month_num": month_num,
#             "year":      year
#         }, as_dict=1)

#         result = {r.main_group: flt(r.target_amount) for r in rows}
#         _target_cache[cache_key] = result
#         return result

#     except Exception:
#         pass

#     # -------------------------------------------------------------------
#     # Strategy 4: fiscal_year as a string e.g. '2026' on parent
#     # -------------------------------------------------------------------
#     try:
#         rows = frappe.db.sql("""
#             SELECT
#                 mtd.main_group,
#                 mtd.target_amount
#             FROM `tabMonthly Target Detail` mtd
#             INNER JOIN `tabSales Person Target` spt
#                 ON spt.name = mtd.parent
#             WHERE spt.sales_person  = %(tso_name)s
#               AND mtd.month         = %(month_num)s
#               AND spt.fiscal_year   = %(year)s
#               AND spt.docstatus     = 1
#         """, {
#             "tso_name":  tso_name,
#             "month_num": month_num,
#             "year":      str(year)      # fiscal_year is often stored as varchar
#         }, as_dict=1)

#         result = {r.main_group: flt(r.target_amount) for r in rows}
#         _target_cache[cache_key] = result
#         return result

#     except Exception:
#         pass

#     # -------------------------------------------------------------------
#     # Fallback: no target found — return empty dict so report still runs
#     # -------------------------------------------------------------------
#     _target_cache[cache_key] = {}
#     return {}


# def get_month_target_from_sales_team(sales_person, month_num, year, category):
#     """Return the target amount for one TSO + month + year + category."""
#     targets = _load_targets_for_tso(sales_person, month_num, year)
#     return flt(targets.get(category, 0))


# # ─────────────────────────────────────────────
# # DATA
# # ─────────────────────────────────────────────
# def get_data(filters, categories):
#     # Reset cache for each report run
#     global _target_cache
#     _target_cache = {}

#     conditions = []
#     values = {}
    
#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")
#         values["from_date"] = filters.get("from_date")
    
#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")
#         values["to_date"] = filters.get("to_date")
    
#     if filters.get("parent_sales_person"):
#         conditions.append("sp.parent_sales_person = %(parent_sales_person)s")
#         values["parent_sales_person"] = filters.get("parent_sales_person")
    
#     if filters.get("sales_person"):
#         conditions.append("sp.name = %(sales_person)s")
#         values["sales_person"] = filters.get("sales_person")
    
#     if filters.get("customer"):
#         conditions.append("si.customer = %(customer)s")
#         values["customer"] = filters.get("customer")
    
#     if filters.get("customer_group"):
#         conditions.append("si.customer_group = %(customer_group)s")
#         values["customer_group"] = filters.get("customer_group")

#     if filters.get("custom_region"):
#         regions = filters.custom_region
#         if isinstance(regions, str):
#             regions = [x.strip() for x in regions.split(",") if x.strip()]
#         if regions:
#             conditions.append("sp.custom_region IN %(custom_region)s")
#             values["custom_region"] = tuple(regions)

#     if filters.get("custom_head_sales_code"):
#         codes = filters.custom_head_sales_code
#         if isinstance(codes, str):
#             codes = [x.strip() for x in codes.split(",") if x.strip()]
#         if codes:
#             conditions.append("sp.custom_head_sales_code IN %(custom_head_sales_code)s")
#             values["custom_head_sales_code"] = tuple(codes)

#     if filters.get("custom_main_group"):
#         cat_filter = filters.custom_main_group
#         if isinstance(cat_filter, str):
#             cat_filter = [x.strip() for x in cat_filter.split(",") if x.strip()]
#         if cat_filter:
#             conditions.append("i.custom_main_group IN %(custom_main_group)s")
#             values["custom_main_group"] = tuple(cat_filter)

#     where_clause = " AND ".join(conditions) if conditions else "1=1"

#     group_by = """
#         DATE_FORMAT(si.posting_date, '%%Y-%%m'),
#         MONTH(si.posting_date),
#         YEAR(si.posting_date),
#         sp.name,
#         sp.parent_sales_person,
#         sp.custom_region,
#         c.customer_name,
#         i.custom_main_group
#     """

#     if filters.get("show_item_details"):
#         group_by += ", sii.item_code, i.item_name"

#     query = f"""
#         SELECT
#             DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month_key,
#             MONTH(si.posting_date)                  AS month_num,
#             YEAR(si.posting_date)                   AS year,
#             sp.name                                 AS tso_name,
#             sp.parent_sales_person,
#             sp.custom_region,
#             c.customer_name,
#             i.custom_main_group                     AS category,
#             sii.item_code,
#             i.item_name,
#             SUM(sii.base_net_amount)                AS achieved,
#             COUNT(DISTINCT si.name)                 AS invoice_count,
#             COUNT(DISTINCT sii.item_code)           AS item_count
#         FROM `tabSales Invoice` si
#         INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
#         INNER JOIN `tabItem` i                 ON i.name = sii.item_code
#         INNER JOIN `tabSales Team` st          ON st.parent = si.name AND st.idx = 1
#         INNER JOIN `tabSales Person` sp        ON sp.name = st.sales_person
#         INNER JOIN `tabCustomer` c             ON c.name = si.customer
#         WHERE si.docstatus = 1
#           AND i.custom_main_group IS NOT NULL
#           AND i.custom_main_group != ''
#           AND {where_clause}
#         GROUP BY {group_by}
#         ORDER BY YEAR(si.posting_date), MONTH(si.posting_date), sp.name
#     """

#     data = frappe.db.sql(query, values, as_dict=1)

#     result = {}

#     for row in data:
#         if filters.get("show_item_details"):
#             key = (row.month_key, row.tso_name, row.customer_name,
#                    row.parent_sales_person, row.custom_region, row.item_code)
#         else:
#             key = (row.month_key, row.tso_name, row.customer_name,
#                    row.parent_sales_person, row.custom_region)

#         if key not in result:
#             entry = {
#                 "month":               f"{MONTHS[int(row.month_num)-1]}-{row.year}",
#                 "month_num":           row.month_num,
#                 "year":                row.year,
#                 "tso_name":            row.tso_name or "Unassigned",
#                 "customer_name":       row.customer_name or "No Customer",
#                 "parent_sales_person": row.parent_sales_person or "Unassigned",
#                 "custom_region":       row.custom_region or "No Region",
#                 "total_achieved":      0,
#                 "total_target":        0,
#                 "invoice_count":       0,
#                 "item_count":          0
#             }

#             if filters.get("show_item_details"):
#                 entry["item_code"] = row.item_code
#                 entry["item_name"] = row.item_name

#             for cat in categories:
#                 safe = cat.replace(" ", "_").replace("-", "_")
#                 entry[f"{safe}_achieved"] = 0
#                 target_value = get_month_target_from_sales_team(
#                     row.tso_name, row.month_num, row.year, cat
#                 )
#                 entry[f"{safe}_target"]  = flt(target_value)
#                 entry["total_target"]   += flt(target_value)

#             result[key] = entry

#         safe = row.category.replace(" ", "_").replace("-", "_")
#         result[key][f"{safe}_achieved"] += flt(row.achieved)
#         result[key]["total_achieved"]   += flt(row.achieved)
#         result[key]["invoice_count"]    += int(row.invoice_count)
#         result[key]["item_count"]       += int(row.item_count)

#     return list(result.values())


# # ─────────────────────────────────────────────
# # CHART
# # ─────────────────────────────────────────────
# def get_chart_data(data, categories):
#     if not data:
#         return None

#     month_totals = {}
#     for row in data:
#         m = row.get("month")
#         month_totals[m] = month_totals.get(m, 0) + flt(row.get("total_achieved"))

#     return {
#         "data": {
#             "labels": list(month_totals.keys()),
#             "datasets": [{"name": "Achieved", "values": list(month_totals.values())}]
#         },
#         "type": "bar",
#         "height": 300
#     }


# # ─────────────────────────────────────────────
# # SUMMARY
# # ─────────────────────────────────────────────
# def get_summary(data, categories):
#     total_achieved = total_target = total_invoice = total_item = 0

#     for row in data:
#         total_achieved += flt(row.get("total_achieved"))
#         total_target   += flt(row.get("total_target"))
#         total_invoice  += flt(row.get("invoice_count"))
#         total_item     += flt(row.get("item_count"))

#     return [
#         {"label": _("Total Achieved"), "value": total_achieved, "indicator": "Green",  "datatype": "Currency"},
#         {"label": _("Total Target"),   "value": total_target,   "indicator": "Blue",   "datatype": "Currency"},
#         {"label": _("Invoice Count"),  "value": total_invoice,  "indicator": "Orange", "datatype": "Int"},
#         {"label": _("Item Count"),     "value": total_item,     "indicator": "Purple", "datatype": "Int"},
#     ]


import frappe
from frappe.utils import flt, getdate
from frappe import _

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

# Map month number to child table fieldname
MONTH_FIELD_MAP = {
    1:  "jan_target",
    2:  "feb_target",
    3:  "mar_target",
    4:  "apr_target",
    5:  "may_target",
    6:  "jun_target",
    7:  "jul_target",
    8:  "aug_target",
    9:  "sep_target",
    10: "oct_target",
    11: "nov_target",
    12: "dec_target"
}

def execute(filters=None):
    filters = frappe._dict(filters or {})

    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date must be before To Date"))

    categories = get_categories(filters)
    columns    = get_columns(categories, filters)
    data       = get_data(filters, categories)
    chart      = get_chart_data(data, categories)
    summary    = get_summary(data, categories)

    return columns, data, None, chart, summary


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
def get_categories(filters):
    if filters.get("custom_main_group"):
        if isinstance(filters.custom_main_group, list):
            return filters.custom_main_group
        return [filters.custom_main_group]

    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    categories = frappe.db.sql("""
        SELECT DISTINCT i.custom_main_group
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        INNER JOIN `tabItem` i ON i.name = sii.item_code
        WHERE si.docstatus = 1
          AND i.custom_main_group IS NOT NULL
          AND i.custom_main_group != ''
          {conditions}
        ORDER BY i.custom_main_group
    """.format(conditions=conditions), values)

    return [c[0] for c in categories if c[0]]


# ─────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────
def get_columns(categories, filters=None):
    columns = []

    if filters and filters.get("show_item_details"):
        columns.extend([
            {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
            {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200}
        ])

    columns.extend([
        {"label": _("Month"),              "fieldname": "month",               "fieldtype": "Data",     "width": 100, "align": "center"},
        {"label": _("TSO"),                "fieldname": "tso_name",            "fieldtype": "Link",     "options": "Sales Person", "width": 200},
        {"label": _("Customer Name"),      "fieldname": "customer_name",       "fieldtype": "Data",     "width": 200},
        {"label": _("Region"),             "fieldname": "custom_region",       "fieldtype": "Data",     "width": 150},
        {"label": _("Head Sales Person"),  "fieldname": "parent_sales_person", "fieldtype": "Link",     "options": "Sales Person", "width": 200},
        {"label": _("Total Achieved"),     "fieldname": "total_achieved",      "fieldtype": "Currency", "width": 150},
        {"label": _("Total Target"),       "fieldname": "total_target",        "fieldtype": "Currency", "width": 150}
    ])

    for cat in categories:
        safe = cat.replace(" ", "_").replace("-", "_")
        columns.append({"label": _(f"{cat} (Target)"),   "fieldname": f"{safe}_target",   "fieldtype": "Currency"})
        columns.append({"label": _(f"{cat} (Achieved)"), "fieldname": f"{safe}_achieved", "fieldtype": "Currency"})

    return columns


# ─────────────────────────────────────────────
# TARGET CACHE
# ─────────────────────────────────────────────
_target_cache = {}

def _load_targets_for_tso(tso_name, month_num, year):
    """
    Load all main_group targets for a given TSO + month + year.
    Monthly Target Detail has columns: main_group, jan_target ... dec_target
    Parent Sales Person Target has: sales_person, year (or fiscal_year)
    Returns dict { main_group: target_amount }
    """
    cache_key = (tso_name, month_num, year)
    if cache_key in _target_cache:
        return _target_cache[cache_key]

    month_field = MONTH_FIELD_MAP.get(int(month_num), "jan_target")

    # ── Try 1: spt.year + spt.sales_person ──────────────────────────────
    try:
        rows = frappe.db.sql(f"""
            SELECT
                mtd.main_group,
                mtd.{month_field} AS target_amount
            FROM `tabMonthly Target Detail` mtd
            INNER JOIN `tabSales Person Target` spt
                ON spt.name = mtd.parent
            WHERE spt.sales_person = %(tso_name)s
              AND spt.year         = %(year)s
              AND spt.docstatus    = 1
        """, {"tso_name": tso_name, "year": year}, as_dict=1)

        result = {r.main_group: flt(r.target_amount) for r in rows if r.main_group}
        _target_cache[cache_key] = result
        return result
    except Exception:
        pass

    # ── Try 2: spt.fiscal_year (varchar) + spt.sales_person ─────────────
    try:
        rows = frappe.db.sql(f"""
            SELECT
                mtd.main_group,
                mtd.{month_field} AS target_amount
            FROM `tabMonthly Target Detail` mtd
            INNER JOIN `tabSales Person Target` spt
                ON spt.name = mtd.parent
            WHERE spt.sales_person = %(tso_name)s
              AND spt.fiscal_year  = %(year)s
              AND spt.docstatus    = 1
        """, {"tso_name": tso_name, "year": str(year)}, as_dict=1)

        result = {r.main_group: flt(r.target_amount) for r in rows if r.main_group}
        _target_cache[cache_key] = result
        return result
    except Exception:
        pass

    # ── Try 3: no year filter on parent (single active doc per TSO) ──────
    try:
        rows = frappe.db.sql(f"""
            SELECT
                mtd.main_group,
                mtd.{month_field} AS target_amount
            FROM `tabMonthly Target Detail` mtd
            INNER JOIN `tabSales Person Target` spt
                ON spt.name = mtd.parent
            WHERE spt.sales_person = %(tso_name)s
              AND spt.docstatus    = 1
        """, {"tso_name": tso_name}, as_dict=1)

        result = {r.main_group: flt(r.target_amount) for r in rows if r.main_group}
        _target_cache[cache_key] = result
        return result
    except Exception:
        pass

    _target_cache[cache_key] = {}
    return {}


def get_month_target_from_sales_team(sales_person, month_num, year, category):
    targets = _load_targets_for_tso(sales_person, month_num, year)
    return flt(targets.get(category, 0))


# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
def get_data(filters, categories):
    global _target_cache
    _target_cache = {}

    conditions = []
    values = {}

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    if filters.get("parent_sales_person"):
        conditions.append("sp.parent_sales_person = %(parent_sales_person)s")
        values["parent_sales_person"] = filters.get("parent_sales_person")

    if filters.get("sales_person"):
        conditions.append("sp.name = %(sales_person)s")
        values["sales_person"] = filters.get("sales_person")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("customer_group"):
        conditions.append("si.customer_group = %(customer_group)s")
        values["customer_group"] = filters.get("customer_group")

    if filters.get("custom_region"):
        regions = filters.custom_region
        if isinstance(regions, str):
            regions = [x.strip() for x in regions.split(",") if x.strip()]
        if regions:
            conditions.append("sp.custom_region IN %(custom_region)s")
            values["custom_region"] = tuple(regions)

    if filters.get("custom_head_sales_code"):
        codes = filters.custom_head_sales_code
        if isinstance(codes, str):
            codes = [x.strip() for x in codes.split(",") if x.strip()]
        if codes:
            conditions.append("sp.custom_head_sales_code IN %(custom_head_sales_code)s")
            values["custom_head_sales_code"] = tuple(codes)

    if filters.get("custom_main_group"):
        cat_filter = filters.custom_main_group
        if isinstance(cat_filter, str):
            cat_filter = [x.strip() for x in cat_filter.split(",") if x.strip()]
        if cat_filter:
            conditions.append("i.custom_main_group IN %(custom_main_group)s")
            values["custom_main_group"] = tuple(cat_filter)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    group_by = """
        DATE_FORMAT(si.posting_date, '%%Y-%%m'),
        MONTH(si.posting_date),
        YEAR(si.posting_date),
        sp.name,
        sp.parent_sales_person,
        sp.custom_region,
        c.customer_name,
        i.custom_main_group
    """

    if filters.get("show_item_details"):
        group_by += ", sii.item_code, i.item_name"

    query = f"""
        SELECT
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month_key,
            MONTH(si.posting_date)                  AS month_num,
            YEAR(si.posting_date)                   AS year,
            sp.name                                 AS tso_name,
            sp.parent_sales_person,
            sp.custom_region,
            c.customer_name,
            i.custom_main_group                     AS category,
            sii.item_code,
            i.item_name,
            SUM(sii.base_net_amount)                AS achieved,
            COUNT(DISTINCT si.name)                 AS invoice_count,
            COUNT(DISTINCT sii.item_code)           AS item_count
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        INNER JOIN `tabItem` i                 ON i.name = sii.item_code
        INNER JOIN `tabSales Team` st          ON st.parent = si.name AND st.idx = 1
        INNER JOIN `tabSales Person` sp        ON sp.name = st.sales_person
        INNER JOIN `tabCustomer` c             ON c.name = si.customer
        WHERE si.docstatus = 1
          AND i.custom_main_group IS NOT NULL
          AND i.custom_main_group != ''
          AND {where_clause}
        GROUP BY {group_by}
        ORDER BY YEAR(si.posting_date), MONTH(si.posting_date), sp.name
    """

    data = frappe.db.sql(query, values, as_dict=1)
    result = {}

    for row in data:
        if filters.get("show_item_details"):
            key = (row.month_key, row.tso_name, row.customer_name,
                   row.parent_sales_person, row.custom_region, row.item_code)
        else:
            key = (row.month_key, row.tso_name, row.customer_name,
                   row.parent_sales_person, row.custom_region)

        if key not in result:
            entry = {
                "month":               f"{MONTHS[int(row.month_num)-1]}-{row.year}",
                "month_num":           row.month_num,
                "year":                row.year,
                "tso_name":            row.tso_name or "Unassigned",
                "customer_name":       row.customer_name or "No Customer",
                "parent_sales_person": row.parent_sales_person or "Unassigned",
                "custom_region":       row.custom_region or "No Region",
                "total_achieved":      0,
                "total_target":        0,
                "invoice_count":       0,
                "item_count":          0
            }

            if filters.get("show_item_details"):
                entry["item_code"] = row.item_code
                entry["item_name"] = row.item_name

            for cat in categories:
                safe = cat.replace(" ", "_").replace("-", "_")
                entry[f"{safe}_achieved"] = 0
                target_value = get_month_target_from_sales_team(
                    row.tso_name, row.month_num, row.year, cat
                )
                entry[f"{safe}_target"]  = flt(target_value)
                entry["total_target"]   += flt(target_value)

            result[key] = entry

        safe = row.category.replace(" ", "_").replace("-", "_")
        result[key][f"{safe}_achieved"] += flt(row.achieved)
        result[key]["total_achieved"]   += flt(row.achieved)
        result[key]["invoice_count"]    += int(row.invoice_count)
        result[key]["item_count"]       += int(row.item_count)

    return list(result.values())


# ─────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────
def get_chart_data(data, categories):
    if not data:
        return None

    month_totals = {}
    for row in data:
        m = row.get("month")
        month_totals[m] = month_totals.get(m, 0) + flt(row.get("total_achieved"))

    return {
        "data": {
            "labels": list(month_totals.keys()),
            "datasets": [{"name": "Achieved", "values": list(month_totals.values())}]
        },
        "type": "bar",
        "height": 300
    }


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
def get_summary(data, categories):
    total_achieved = total_target = total_invoice = total_item = 0

    for row in data:
        total_achieved += flt(row.get("total_achieved"))
        total_target   += flt(row.get("total_target"))
        total_invoice  += flt(row.get("invoice_count"))
        total_item     += flt(row.get("item_count"))

    return [
        {"label": _("Total Achieved"), "value": total_achieved, "indicator": "Green",  "datatype": "Currency"},
        {"label": _("Total Target"),   "value": total_target,   "indicator": "Blue",   "datatype": "Currency"},
        {"label": _("Invoice Count"),  "value": total_invoice,  "indicator": "Orange", "datatype": "Int"},
        {"label": _("Item Count"),     "value": total_item,     "indicator": "Purple", "datatype": "Int"},
    ]