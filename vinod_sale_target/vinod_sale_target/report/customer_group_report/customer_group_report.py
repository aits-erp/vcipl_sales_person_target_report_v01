# # Copyright (c) 2026, Sukku and contributors
# # For license information, please see license.txt
# #
# # CUSTOMER GROUP REPORT  =  exact copy of TEST REPORT.
# #
# # The ONLY differences (all marked with  # >>> CHANGED) are the ones needed so that
# # no Sales Invoice value is dropped, so figures match "Sales Analytic Dashboard":
# #   1. Items with a blank Main Group are no longer removed          -> shown as "Unmapped"
# #   2. Main Groups that are not in the category list are no longer ignored
# #      -> they get their own column automatically
# #   3. LEFT JOIN on Item / Customer (INNER JOIN used to drop lines)
# #   4. Total Achieved counts every category (the "target > 0" rule for
# #      Debtors Distributors is removed - it hid sales from the Total)
# #   5. Opening invoices (is_opening = 'Yes') are excluded, same as Sales Analytics

# import io
# import frappe
# from frappe import _
# from frappe.utils import flt, getdate

# from openpyxl import Workbook
# from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
# from openpyxl.chart import BarChart, Reference
# from openpyxl.utils import get_column_letter


# MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
#           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# MONTH_FIELD_MAP = {
#     1: "jan_target", 2: "feb_target", 3: "mar_target",
#     4: "apr_target", 5: "may_target", 6: "jun_target",
#     7: "jul_target", 8: "aug_target", 9: "sep_target",
#     10: "oct_target", 11: "nov_target", 12: "dec_target"
# }

# DEFAULT_CATEGORIES = [
#     "Nonstick",
#     "Horeca",
#     "Pressure Cookers",
#     "SS Cookware",
#     "Healux",
#     "Kraft",
#     "Platinum",
#     "Platinum Triply P.cooker",
#     "Cast Iron",
#     "Bottle",
#     "Csd",
#     "Other",
#     "Futuretec"
# ]

# DISPLAY_ONLY_CATEGORIES = [
#     "Freya Cast Iron",
# ]

# # >>> CHANGED: bucket for items that have no Main Group
# UNMAPPED = "Unmapped"
# CAT_EXPR = "COALESCE(NULLIF(TRIM(i.custom_main_group), ''), 'Unmapped')"

# SECTION_VIEW_MAP = {
#     "North Detail":      (["parent_sales_person"], ["Rajiv K Dutta"]),
#     "East Detail":       (["parent_sales_person"], ["Pannalal Bhattacharya"]),
#     "South Detail":      (["parent_sales_person"], ["Mohammed Muqeemudheen Cherayakkuth"]),
#     "ROM Detail":        (["parent_sales_person"], ["Sandeep Kumar"]),
#     "MPCG Detail":       (["parent_sales_person", "tso_name"], ["Jaydeo Deshmukh"]),
#     "Mumbai AH Detail":  (["parent_sales_person"], ["Muslim Abdulla Hakim (Aslam)"]),
#     "Gujarat Detail":    (["tso_name", "parent_sales_person"], ["MAYUR TALATI"]),
# }

# _target_cache = {}


# def safe_field(category):
#     # >>> CHANGED: also strip / & ( ) so newly found category names stay valid field names
#     return (
#         category.replace(" ", "_").replace("-", "_")
#         .replace("/", "_").replace("&", "_").replace("(", "_").replace(")", "_")
#     )


# def normalize(value):
#     return (value or "").strip().casefold()


# def row_matches_section(row, fieldnames, selected_values):
#     normalized_targets = {normalize(v) for v in selected_values}
#     for fieldname in fieldnames:
#         if normalize(row.get(fieldname)) in normalized_targets:
#             return True
#     return False


# def filter_section_rows(rows, fieldnames, selected_values):
#     return [r for r in rows if row_matches_section(r, fieldnames, selected_values)]


# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     if filters.get("from_date") and filters.get("to_date"):
#         if getdate(filters.from_date) > getdate(filters.to_date):
#             frappe.throw(_("From Date must be before To Date"))

#     categories = get_categories(filters)
#     raw_data   = get_data(filters, categories)
#     view_type  = filters.get("view_type") or "TSO Summary"

#     if view_type == "Region Summary":
#         columns = get_region_summary_columns()
#         data    = get_region_summary_data(raw_data)

#     elif view_type in SECTION_VIEW_MAP:
#         fieldnames, selected_values = SECTION_VIEW_MAP[view_type]
#         columns = get_columns(categories, filters)
#         data    = filter_section_rows(raw_data, fieldnames, selected_values)

#     else:
#         columns = get_columns(categories, filters)
#         data    = raw_data

#     return columns, data


# def parse_multi(value):
#     if not value:
#         return []
#     if isinstance(value, list):
#         return value
#     return [x.strip() for x in str(value).split(",") if x.strip()]


# def get_customer_group_list(customer_group):
#     """Selected group + every child group under it (Customer Group is a tree)."""
#     if not customer_group:
#         return []
#     vals = frappe.db.get_value("Customer Group", customer_group, ["lft", "rgt"])
#     if not vals:
#         return [customer_group]
#     lft, rgt = vals
#     names = frappe.get_all(
#         "Customer Group",
#         filters={"lft": [">=", lft], "rgt": ["<=", rgt]},
#         pluck="name"
#     )
#     return names or [customer_group]


# # >>> CHANGED: category list = the ones in the filter / defaults (same as Test Report)
# #              PLUS every other Main Group that really has sales in the period
# #              PLUS "Unmapped" when some items have no Main Group.
# def get_extra_categories(filters):
#     conditions = ["si.docstatus = 1", "IFNULL(si.is_opening, 'No') = 'No'"]
#     values     = {}

#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")
#         values["from_date"] = filters.get("from_date")

#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")
#         values["to_date"] = filters.get("to_date")

#     if filters.get("customer"):
#         conditions.append("si.customer = %(customer)s")
#         values["customer"] = filters.get("customer")

#     if filters.get("customer_group"):
#         conditions.append("si.customer_group IN %(customer_group)s")
#         values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

#     rows = frappe.db.sql(f"""
#         SELECT DISTINCT {CAT_EXPR} AS category
#         FROM `tabSales Invoice` si
#         INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
#         LEFT JOIN `tabItem` i ON i.name = sii.item_code
#         WHERE {" AND ".join(conditions)}
#     """, values, as_dict=1)

#     found = sorted({r.category for r in rows if r.category and r.category != UNMAPPED},
#                    key=lambda x: x.casefold())
#     if any(r.category == UNMAPPED for r in rows):
#         found.append(UNMAPPED)
#     return found


# def get_categories(filters):
#     if filters.get("custom_main_group"):
#         if isinstance(filters.custom_main_group, list):
#             base = list(filters.custom_main_group)
#         else:
#             base = [x.strip() for x in str(filters.custom_main_group).split(",") if x.strip()]
#     else:
#         base = list(DEFAULT_CATEGORIES)

#     seen = {normalize(c) for c in base}
#     for cat in get_extra_categories(filters):
#         if normalize(cat) not in seen:
#             base.append(cat)
#             seen.add(normalize(cat))
#     return base


# def get_columns(categories, filters=None):
#     columns = []

#     if filters and filters.get("show_item_details"):
#         columns.extend([
#             {"label": _("Item Code"), "fieldname": "item_code",
#              "fieldtype": "Link", "options": "Item", "width": 150},
#             {"label": _("Item Name"), "fieldname": "item_name",
#              "fieldtype": "Data", "width": 200}
#         ])

#     columns.extend([
#         {"label": _("Month"),            "fieldname": "month",               "fieldtype": "Data",     "width": 100},
#         {"label": _("TSO"),              "fieldname": "tso_name",            "fieldtype": "Data",     "width": 200},
#         {"label": _("Customer Name"),    "fieldname": "customer_name",       "fieldtype": "Data",     "width": 220},
#         {"label": _("Customer Group"),   "fieldname": "customer_group",      "fieldtype": "Data",     "width": 200},
#         {"label": _("Region"),           "fieldname": "custom_region",       "fieldtype": "Data",     "width": 130},
#         {"label": _("Territory Code"),   "fieldname": "custom_territory",    "fieldtype": "Data",     "width": 130},
#         {"label": _("Head Sales Person"),"fieldname": "parent_sales_person", "fieldtype": "Data",     "width": 200},
#         {"label": _("Total Achieved"),   "fieldname": "total_achieved",      "fieldtype": "Currency", "width": 150},
#         {"label": _("Total Target"),     "fieldname": "total_target",        "fieldtype": "Currency", "width": 150},
#         {"label": _("Achievement %"),    "fieldname": "achievement_percent", "fieldtype": "Percent",  "width": 120},
#     ])

#     for cat in categories:
#         safe = safe_field(cat)
#         columns.append({"label": _(f"{cat} Target"),   "fieldname": f"{safe}_target",
#                          "fieldtype": "Currency", "width": 130})
#         columns.append({"label": _(f"{cat} Achieved"), "fieldname": f"{safe}_achieved",
#                          "fieldtype": "Currency", "width": 130})

#     return columns


# def get_region_summary_columns():
#     return [
#         {"label": _("Region"),         "fieldname": "region",              "fieldtype": "Data",     "width": 180},
#         {"label": _("Target"),         "fieldname": "target",              "fieldtype": "Currency", "width": 150},
#         {"label": _("Achieved"),       "fieldname": "achieved",            "fieldtype": "Currency", "width": 150},
#         {"label": _("Gap"),            "fieldname": "gap",                 "fieldtype": "Currency", "width": 150},
#         {"label": _("Achievement %"),  "fieldname": "achievement_percent", "fieldtype": "Percent",  "width": 120},
#     ]


# def _load_targets_for_customer(customer, month_num):
#     cache_key = (customer, month_num)
#     if cache_key in _target_cache:
#         return _target_cache[cache_key]

#     month_field = MONTH_FIELD_MAP.get(int(month_num), "jan_target")

#     try:
#         rows = frappe.db.sql(f"""
#             SELECT
#                 mtd.main_group,
#                 mtd.{month_field} AS target_amount
#             FROM `tabMonthly Target Detail` mtd
#             INNER JOIN `tabSales Person Target` spt
#                 ON spt.name = mtd.parent
#             WHERE spt.name        = %(customer)s
#               AND spt.period_type = 'Monthly'
#               AND spt.docstatus   IN (0, 1)
#         """, {"customer": customer}, as_dict=1)

#         result = {r.main_group: flt(r.target_amount) for r in rows if r.main_group}
#         _target_cache[cache_key] = result
#         return result

#     except Exception as e:
#         frappe.log_error(f"Target fetch error for customer {customer}: {e}", "CUSTOMER GROUP REPORT")

#     _target_cache[cache_key] = {}
#     return {}


# def get_target_for_customer_category(customer, month_num, category):
#     targets = _load_targets_for_customer(customer, month_num)
#     return flt(targets.get(category, 0))


# def get_display_only_category_totals(filters, category):
#     conditions = ["si.docstatus = 1", "i.custom_main_group = %(category)s"]
#     values     = {"category": category}

#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")
#         values["from_date"] = filters.get("from_date")

#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")
#         values["to_date"] = filters.get("to_date")

#     if filters.get("customer_group"):
#         conditions.append("si.customer_group IN %(customer_group)s")
#         values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

#     where_clause = " AND ".join(conditions)

#     row = frappe.db.sql(f"""
#         SELECT COALESCE(SUM(sii.base_net_amount), 0) AS achieved
#         FROM `tabSales Invoice` si
#         INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
#         INNER JOIN `tabItem` i ON i.name = sii.item_code
#         WHERE {where_clause}
#     """, values, as_dict=1)

#     return flt(row[0].achieved) if row else 0


# def get_achieved_data(filters, categories):
#     global _target_cache
#     _target_cache = {}

#     # >>> CHANGED: opening invoices excluded (same as Sales Analytics dashboard)
#     conditions = ["si.docstatus = 1", "IFNULL(si.is_opening, 'No') = 'No'"]
#     values     = {}

#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")
#         values["from_date"] = filters.get("from_date")

#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")
#         values["to_date"] = filters.get("to_date")

#     # filter uses sp_cust only (Customer master TSO)
#     if filters.get("sales_person"):
#         conditions.append("sp_cust.name = %(sales_person)s")
#         values["sales_person"] = filters.get("sales_person")

#     if filters.get("parent_sales_person"):
#         conditions.append("sp_cust.parent_sales_person = %(parent_sales_person)s")
#         values["parent_sales_person"] = filters.get("parent_sales_person")

#     if filters.get("customer"):
#         conditions.append("si.customer = %(customer)s")
#         values["customer"] = filters.get("customer")

#     if filters.get("customer_group"):
#         conditions.append("si.customer_group IN %(customer_group)s")
#         values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

#     regions = parse_multi(filters.get("custom_region"))
#     if regions:
#         conditions.append("sp_cust.custom_region IN %(custom_region)s")
#         values["custom_region"] = tuple(regions)

#     territories = parse_multi(filters.get("custom_territory"))
#     if territories:
#         conditions.append("sp_cust.custom_territory IN %(custom_territory)s")
#         values["custom_territory"] = tuple(territories)

#     codes = parse_multi(filters.get("custom_head_sales_code"))
#     if codes:
#         conditions.append("sp_cust.custom_head_sales_code IN %(custom_head_sales_code)s")
#         values["custom_head_sales_code"] = tuple(codes)

#     # >>> CHANGED: the Category filter no longer removes sales in SQL.
#     #     It only decides which columns are shown first; every other category
#     #     is added as an extra column, so nothing is lost from the Total.

#     where_clause = " AND ".join(conditions)

#     group_by = f"""
#         DATE_FORMAT(si.posting_date, '%%Y-%%m'),
#         MONTH(si.posting_date),
#         YEAR(si.posting_date),
#         si.customer,
#         si.customer_group,
#         sp_cust.name,
#         sp_cust.parent_sales_person,
#         sp_cust.custom_region,
#         sp_cust.custom_territory,
#         sp_cust.custom_head_sales_code,
#         c.customer_name,
#         {CAT_EXPR}
#     """

#     if filters.get("show_item_details"):
#         item_cols = "sii.item_code AS item_code, i.item_name AS item_name,"
#         group_by += ", sii.item_code, i.item_name"
#     else:
#         item_cols = "'' AS item_code, '' AS item_name,"

#     # >>> CHANGED: LEFT JOIN Item / Customer, no custom_main_group IS NOT NULL / != '' filter
#     query = f"""
#         SELECT
#             DATE_FORMAT(si.posting_date, '%%Y-%%m')  AS month_key,
#             MONTH(si.posting_date)                    AS month_num,
#             YEAR(si.posting_date)                     AS year,
#             si.customer                               AS customer,
#             si.customer_group                         AS customer_group,
#             COALESCE(sp_cust.name, 'Unassigned')      AS tso_name,
#             COALESCE(sp_cust.parent_sales_person, '')  AS parent_sales_person,
#             COALESCE(sp_cust.custom_region, '')        AS custom_region,
#             COALESCE(sp_cust.custom_territory, '')     AS custom_territory,
#             COALESCE(sp_cust.custom_head_sales_code, '') AS custom_head_sales_code,
#             c.customer_name                           AS customer_name,
#             {CAT_EXPR}                                AS category,
#             {item_cols}
#             SUM(sii.base_net_amount)                  AS achieved,
#             COUNT(DISTINCT si.name)                   AS invoice_count,
#             COUNT(DISTINCT sii.item_code)             AS item_count
#         FROM `tabSales Invoice` si
#         INNER JOIN `tabSales Invoice Item` sii
#             ON sii.parent = si.name
#         LEFT JOIN `tabItem` i
#             ON i.name = sii.item_code
#         LEFT JOIN `tabCustomer` c
#             ON c.name = si.customer

#         -- ONLY Customer master Sales Team, idx=1 to prevent duplicates
#         LEFT JOIN `tabSales Team` st_cust
#             ON st_cust.parent      = si.customer
#             AND st_cust.parenttype = 'Customer'
#             AND st_cust.idx        = 1

#         LEFT JOIN `tabSales Person` sp_cust
#             ON sp_cust.name = st_cust.sales_person

#         WHERE {where_clause}
#         GROUP BY {group_by}
#         ORDER BY
#             YEAR(si.posting_date),
#             MONTH(si.posting_date),
#             sp_cust.custom_region,
#             sp_cust.name,
#             c.customer_name
#     """

#     rows       = frappe.db.sql(query, values, as_dict=1)
#     result     = {}
#     cat_lookup = {normalize(c): c for c in categories}

#     for row in rows:
#         tso      = row.tso_name or "Unassigned"
#         customer = row.customer

#         # >>> CHANGED: customer_group added to the key so a customer's invoices
#         #     that carry different groups are never merged into the wrong group
#         if filters.get("show_item_details"):
#             key = (row.month_key, customer, tso, row.customer_group, row.item_code)
#         else:
#             key = (row.month_key, customer, tso, row.customer_group)

#         if key not in result:
#             entry = {
#                 "customer":            customer,
#                 "customer_group":      row.customer_group or "",
#                 "month":               f"{MONTHS[int(row.month_num)-1]}-{row.year}",
#                 "month_num":           row.month_num,
#                 "year":                row.year,
#                 "tso_name":            tso,
#                 "customer_name":       row.customer_name or "No Customer",
#                 "parent_sales_person": row.parent_sales_person or "",
#                 "custom_region":       row.custom_region or "",
#                 "custom_territory":    row.custom_territory or "",
#                 "custom_head_sales_code": row.custom_head_sales_code or "",
#                 "total_achieved":      0,
#                 "total_target":        0,
#                 "achievement_percent": 0,
#                 "invoice_count":       0,
#                 "item_count":          0
#             }

#             if filters.get("show_item_details"):
#                 entry["item_code"] = row.item_code
#                 entry["item_name"] = row.item_name

#             for cat in categories:
#                 safe = safe_field(cat)
#                 entry[f"{safe}_achieved"] = 0
#                 target_value = get_target_for_customer_category(
#                     customer, row.month_num, cat
#                 )
#                 entry[f"{safe}_target"]  = flt(target_value)
#                 entry["total_target"]   += flt(target_value)

#             result[key] = entry

#         cat = cat_lookup.get(normalize(row.category))
#         if cat:
#             safe              = safe_field(cat)
#             category_achieved = flt(row.achieved)

#             result[key][f"{safe}_achieved"] += category_achieved

#             # >>> CHANGED: every category counts toward Total Achieved
#             result[key]["total_achieved"] += category_achieved
#             result[key]["invoice_count"]  += int(row.invoice_count or 0)
#             result[key]["item_count"]     += int(row.item_count or 0)

#     return list(result.values())


# def get_month_year_range(from_date, to_date):
#     start = getdate(from_date)
#     end   = getdate(to_date)
#     result = []
#     y, m = start.year, start.month

#     while (y, m) <= (end.year, end.month):
#         result.append((y, m))
#         if m == 12:
#             y += 1
#             m  = 1
#         else:
#             m += 1

#     return result


# def get_target_skeleton_rows(filters, categories, month_year_list):
#     if not categories or not month_year_list:
#         return []

#     conditions = ["spt.period_type = 'Monthly'", "spt.docstatus IN (0, 1)"]
#     values     = {"categories": tuple(categories)}
#     conditions.append("mtd.main_group IN %(categories)s")

#     if filters.get("customer"):
#         conditions.append("spt.name = %(customer)s")
#         values["customer"] = filters.get("customer")

#     if filters.get("customer_group"):
#         conditions.append("c.customer_group IN %(customer_group)s")
#         values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

#     regions = parse_multi(filters.get("custom_region"))
#     if regions:
#         conditions.append("sp_cust.custom_region IN %(custom_region)s")
#         values["custom_region"] = tuple(regions)

#     territories = parse_multi(filters.get("custom_territory"))
#     if territories:
#         conditions.append("sp_cust.custom_territory IN %(custom_territory)s")
#         values["custom_territory"] = tuple(territories)

#     codes = parse_multi(filters.get("custom_head_sales_code"))
#     if codes:
#         conditions.append("sp_cust.custom_head_sales_code IN %(custom_head_sales_code)s")
#         values["custom_head_sales_code"] = tuple(codes)

#     if filters.get("sales_person"):
#         conditions.append("sp_cust.name = %(sales_person)s")
#         values["sales_person"] = filters.get("sales_person")

#     if filters.get("parent_sales_person"):
#         conditions.append("sp_cust.parent_sales_person = %(parent_sales_person)s")
#         values["parent_sales_person"] = filters.get("parent_sales_person")

#     where_clause    = " AND ".join(conditions)
#     month_field_cols = ", ".join(f"mtd.{f}" for f in MONTH_FIELD_MAP.values())

#     rows = frappe.db.sql(f"""
#         SELECT
#             spt.name                                    AS customer,
#             c.customer_name                             AS customer_name,
#             c.customer_group                            AS customer_group,
#             mtd.main_group                              AS category,
#             {month_field_cols},
#             COALESCE(sp_cust.name, 'Unassigned')        AS tso_name,
#             COALESCE(sp_cust.parent_sales_person, '')    AS parent_sales_person,
#             COALESCE(sp_cust.custom_region, '')          AS custom_region,
#             COALESCE(sp_cust.custom_territory, '')       AS custom_territory,
#             COALESCE(sp_cust.custom_head_sales_code, '') AS custom_head_sales_code
#         FROM `tabSales Person Target` spt
#         INNER JOIN `tabMonthly Target Detail` mtd
#             ON mtd.parent = spt.name
#         INNER JOIN `tabCustomer` c
#             ON c.name = spt.name
#         LEFT JOIN `tabSales Team` st_cust
#             ON st_cust.parent      = c.name
#             AND st_cust.parenttype = 'Customer'
#             AND st_cust.idx        = 1
#         LEFT JOIN `tabSales Person` sp_cust
#             ON sp_cust.name = st_cust.sales_person
#         WHERE {where_clause}
#     """, values, as_dict=1)

#     by_customer = {}
#     for r in rows:
#         info = by_customer.setdefault(r.customer, {
#             "customer_name":          r.customer_name or "No Customer",
#             "customer_group":         r.customer_group or "",
#             "tso_name":               r.tso_name,
#             "parent_sales_person":    r.parent_sales_person,
#             "custom_region":          r.custom_region,
#             "custom_territory":       r.custom_territory,
#             "custom_head_sales_code": r.custom_head_sales_code,
#             "categories":             {}
#         })
#         info["categories"][r.category] = r

#     skeleton = {}

#     for customer, info in by_customer.items():
#         for year, month in month_year_list:
#             month_key   = f"{year:04d}-{month:02d}"
#             month_field = MONTH_FIELD_MAP[month]
#             key         = (month_key, customer, info["tso_name"])

#             if key not in skeleton:
#                 entry = {
#                     "customer":               customer,
#                     "month":                  f"{MONTHS[month-1]}-{year}",
#                     "month_num":              month,
#                     "year":                   year,
#                     "tso_name":               info["tso_name"],
#                     "customer_name":          info["customer_name"],
#                     "customer_group":         info["customer_group"],
#                     "parent_sales_person":    info["parent_sales_person"],
#                     "custom_region":          info["custom_region"],
#                     "custom_territory":       info["custom_territory"],
#                     "custom_head_sales_code": info["custom_head_sales_code"],
#                     "total_achieved":         0,
#                     "total_target":           0,
#                     "achievement_percent":    0,
#                     "invoice_count":          0,
#                     "item_count":             0
#                 }

#                 if filters.get("show_item_details"):
#                     entry["item_code"] = ""
#                     entry["item_name"] = ""

#                 for cat in categories:
#                     safe = safe_field(cat)
#                     entry[f"{safe}_achieved"] = 0
#                     entry[f"{safe}_target"]   = 0

#                 skeleton[key] = entry

#             entry = skeleton[key]

#             for cat in categories:
#                 cat_row = info["categories"].get(cat)
#                 if not cat_row:
#                     continue
#                 target_amt = flt(cat_row.get(month_field))
#                 if target_amt:
#                     safe = safe_field(cat)
#                     entry[f"{safe}_target"] += target_amt
#                     entry["total_target"]   += target_amt

#     return list(skeleton.values())


# def get_data(filters, categories):
#     final_data = get_achieved_data(filters, categories)

#     from_date = filters.get("from_date")
#     to_date   = filters.get("to_date")

#     if from_date and to_date:
#         covered_customer_months = set()
#         for row in final_data:
#             covered_customer_months.add((
#                 f'{int(row.get("year")):04d}-{int(row.get("month_num")):02d}',
#                 row.get("customer")
#             ))

#         month_year_list = get_month_year_range(from_date, to_date)
#         skeleton_rows   = get_target_skeleton_rows(filters, categories, month_year_list)

#         for srow in skeleton_rows:
#             skey = (
#                 f'{int(srow.get("year")):04d}-{int(srow.get("month_num")):02d}',
#                 srow.get("customer")
#             )
#             if skey not in covered_customer_months and flt(srow.get("total_target")) > 0:
#                 final_data.append(srow)

#     for row in final_data:
#         row["achievement_percent"] = (
#             flt(row.get("total_achieved")) / flt(row.get("total_target")) * 100
#             if flt(row.get("total_target")) else 0
#         )

#     return final_data


# def get_region_bucket(row):
#     region = (row.get("custom_region") or "").strip()

#     if region in ("North", "South", "East"):
#         return region

#     if row_matches_section(row, *SECTION_VIEW_MAP["ROM Detail"]):
#         return "ROM"
#     if row_matches_section(row, *SECTION_VIEW_MAP["Mumbai AH Detail"]):
#         return "Mumbai AH"
#     if row_matches_section(row, *SECTION_VIEW_MAP["MPCG Detail"]):
#         return "MPCG"
#     if row_matches_section(row, *SECTION_VIEW_MAP["Gujarat Detail"]):
#         return "Gujarat"

#     return region or "Unassigned"


# def get_region_summary_data(data):
#     result = {}

#     for row in data:
#         region = get_region_bucket(row)

#         if region not in result:
#             result[region] = {
#                 "region":  region,
#                 "target":  0,
#                 "achieved": 0,
#                 "gap":     0,
#                 "achievement_percent": 0
#             }

#         result[region]["target"]   += flt(row.get("total_target"))
#         result[region]["achieved"] += flt(row.get("total_achieved"))

#     final = []
#     for region, row in result.items():
#         row["gap"] = row["target"] - row["achieved"]
#         row["achievement_percent"] = (
#             row["achieved"] / row["target"] * 100
#             if row["target"] else 0
#         )
#         final.append(row)

#     return sorted(final, key=lambda x: x["region"])


# def aggregate_party_wise(data, categories):
#     grouped = {}

#     for row in data:
#         # >>> CHANGED: customer_group added to the key (see get_achieved_data)
#         key = (row.get("customer"), row.get("tso_name"), row.get("customer_group"))

#         if key not in grouped:
#             entry = {
#                 "customer":               row.get("customer"),
#                 "customer_name":          row.get("customer_name"),
#                 "customer_group":         row.get("customer_group"),
#                 "tso_name":               row.get("tso_name"),
#                 "parent_sales_person":    row.get("parent_sales_person"),
#                 "custom_region":          row.get("custom_region"),
#                 "custom_territory":       row.get("custom_territory"),
#                 "custom_head_sales_code": row.get("custom_head_sales_code"),
#                 "month":                  "All",
#                 "total_achieved":         0,
#                 "total_target":           0,
#                 "achievement_percent":    0,
#                 "invoice_count":          0,
#                 "item_count":             0
#             }
#             for cat in categories:
#                 safe = safe_field(cat)
#                 entry[f"{safe}_target"]   = 0
#                 entry[f"{safe}_achieved"] = 0

#             grouped[key] = entry

#         entry = grouped[key]
#         entry["total_achieved"] += flt(row.get("total_achieved"))
#         entry["total_target"]   += flt(row.get("total_target"))
#         entry["invoice_count"]  += flt(row.get("invoice_count"))
#         entry["item_count"]     += flt(row.get("item_count"))

#         for cat in categories:
#             safe = safe_field(cat)
#             entry[f"{safe}_target"]   += flt(row.get(f"{safe}_target"))
#             entry[f"{safe}_achieved"] += flt(row.get(f"{safe}_achieved"))

#     result = list(grouped.values())
#     for entry in result:
#         entry["achievement_percent"] = (
#             entry["total_achieved"] / entry["total_target"] * 100
#             if entry["total_target"] else 0
#         )

#     return result


# def get_summary(data, categories):
#     total_achieved = total_target = total_invoice = total_item = 0

#     for row in data:
#         total_achieved += flt(row.get("total_achieved"))
#         total_target   += flt(row.get("total_target"))
#         total_invoice  += flt(row.get("invoice_count"))
#         total_item     += flt(row.get("item_count"))

#     ach_percent = total_achieved / total_target * 100 if total_target else 0

#     return [
#         {"label": _("Total Achieved"), "value": total_achieved, "indicator": "Green",  "datatype": "Currency"},
#         {"label": _("Total Target"),   "value": total_target,   "indicator": "Yellow", "datatype": "Currency"},
#         {"label": _("Achievement %"),  "value": ach_percent,    "indicator": "Purple", "datatype": "Percent"},
#         {"label": _("Invoice Count"),  "value": total_invoice,  "indicator": "Orange", "datatype": "Int"},
#         {"label": _("Item Count"),     "value": total_item,     "indicator": "Grey",   "datatype": "Int"},
#     ]


# def get_chart(data):
#     region_data = get_region_summary_data(data)
#     if not region_data:
#         return None

#     return {
#         "data": {
#             "labels": [d["region"] for d in region_data],
#             "datasets": [
#                 {"name": "Target",   "values": [d["target"]   for d in region_data]},
#                 {"name": "Achieved", "values": [d["achieved"] for d in region_data]}
#             ]
#         },
#         "type": "bar",
#         "height": 280,
#     }


# def get_period_label(filters):
#     from_date = filters.get("from_date")
#     to_date   = filters.get("to_date")
#     if not (from_date and to_date):
#         return "All Data"
#     return f"{frappe.utils.formatdate(from_date)} to {frappe.utils.formatdate(to_date)}"


# @frappe.whitelist()
# def download_mis_excel(**filters):
#     filters      = frappe._dict(filters or {})
#     categories   = get_categories(filters)
#     data         = get_data(filters, categories)
#     view_type    = filters.get("view_type") or "TSO Summary"
#     period_label = get_period_label(filters)
#     party_wise_total = int(filters.get("party_wise_total") or 0)

#     wb = Workbook()

#     if view_type == "Region Summary":
#         ws = wb.active
#         ws.title = "Region Summary"
#         make_region_summary_sheet(ws, data, sheet_label="Region Summary", period_label=period_label)
#         add_region_chart(ws, header_row=3)
#         filename_part = "Region_Summary"

#     elif view_type in SECTION_VIEW_MAP:
#         fieldnames, selected_values = SECTION_VIEW_MAP[view_type]
#         section_rows    = filter_section_rows(data, fieldnames, selected_values)
#         clean_sheet_name = view_type.replace(" Detail", "")[:31]
#         rows_for_sheet  = (
#             aggregate_party_wise(section_rows, categories)
#             if party_wise_total else section_rows
#         )
#         ws = wb.active
#         ws.title = clean_sheet_name
#         make_tso_summary_sheet(
#             ws, rows_for_sheet, categories,
#             sheet_label=f"{clean_sheet_name} — Target vs Achievement",
#             period_label=period_label
#         )
#         filename_part = clean_sheet_name.replace(" ", "_")

#     else:
#         tso_rows = aggregate_party_wise(data, categories) if party_wise_total else data
#         ws = wb.active
#         ws.title = "TSO Summary"
#         make_tso_summary_sheet(
#             ws, tso_rows, categories,
#             sheet_label="TSO Summary — Target vs Achievement",
#             period_label=period_label
#         )

#         ws_region = wb.create_sheet("Region Summary")
#         make_region_summary_sheet(ws_region, data,
#                                   sheet_label="Region Summary", period_label=period_label)

#         ws_chart = wb.create_sheet("Charts")
#         make_region_summary_sheet(ws_chart, data,
#                                   sheet_label="Region Summary (Chart)", period_label=period_label)
#         add_region_chart(ws_chart, header_row=3)

#         for sheet_name, (fieldnames, selected_values) in SECTION_VIEW_MAP.items():
#             clean_sheet_name = sheet_name.replace(" Detail", "")[:31]
#             section_rows     = filter_section_rows(data, fieldnames, selected_values)
#             if section_rows:
#                 rows_for_sheet = (
#                     aggregate_party_wise(section_rows, categories)
#                     if party_wise_total else section_rows
#                 )
#                 ws_sec = wb.create_sheet(clean_sheet_name)
#                 make_tso_summary_sheet(
#                     ws_sec, rows_for_sheet, categories,
#                     sheet_label=f"{clean_sheet_name} — Target vs Achievement",
#                     period_label=period_label
#                 )

#         filename_part = "Full_MIS"

#     output = io.BytesIO()
#     wb.save(output)
#     output.seek(0)

#     frappe.local.response.filename    = f"Vinod_Cookware_{filename_part}.xlsx"
#     frappe.local.response.filecontent = output.read()
#     frappe.local.response.type        = "download"


# def make_tso_summary_sheet(ws, data, categories,
#                             sheet_label="TSO Target vs Achievement",
#                             period_label=None):
#     dark_green  = "0B6A57"
#     yellow      = "FFF2CC"
#     blue        = "DDEBF7"
#     total_fill  = "D9EAD3"
#     period_fill = "E8F5F1"

#     thin   = Side(style="thin", color="999999")
#     border = Border(left=thin, right=thin, top=thin, bottom=thin)

#     headers = ["Region", "TSO", "Distributor", "Customer Group"]
#     for cat in categories:
#         headers.append(f"{cat} Target")
#         headers.append(f"{cat} Achieved")
#     headers += ["Total Target", "Total Achieved", "Achievement %"]
#     ncols = len(headers)

#     ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
#     title = ws.cell(1, 1)
#     title.value     = f"Vinod Cookware — {sheet_label}"
#     title.font      = Font(bold=True, color="FFFFFF", size=12)
#     title.fill      = PatternFill("solid", fgColor=dark_green)
#     title.alignment = Alignment(horizontal="center")

#     ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
#     period_cell       = ws.cell(2, 1)
#     period_cell.value = f"Period: {period_label}" if period_label else "Period: All Data"
#     period_cell.font  = Font(bold=True, color="0B3D5C", size=10)
#     period_cell.fill  = PatternFill("solid", fgColor=period_fill)
#     period_cell.alignment = Alignment(horizontal="center")

#     header_row = 3
#     for col, h in enumerate(headers, 1):
#         cell           = ws.cell(header_row, col)
#         cell.value     = h
#         cell.font      = Font(bold=True, color="FFFFFF")
#         cell.fill      = PatternFill("solid", fgColor=dark_green)
#         cell.border    = border
#         cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

#     # sort so each TSO's customers sit together
#     data = sorted(data, key=lambda r: (
#         (r.get("custom_region") or ""),
#         (r.get("tso_name") or ""),
#         (r.get("customer_name") or "")
#     ))

#     tt_col = get_column_letter(ncols - 2)   # Total Target column letter
#     ta_col = get_column_letter(ncols - 1)   # Total Achieved column letter

#     # writes one "TOTAL — <TSO>" row
#     def write_tso_total(r, tso, region, start, end):
#         ws.cell(r, 1).value = region
#         ws.cell(r, 2).value = tso
#         ws.cell(r, 3).value = f"TOTAL — {tso}"
#         for col in range(5, ncols):
#             L = get_column_letter(col)
#             ws.cell(r, col).value = f"=SUM({L}{start}:{L}{end})"
#         ws.cell(r, ncols).value = f"=IF({tt_col}{r}=0,0,{ta_col}{r}/{tt_col}{r})"
#         for col in range(1, ncols + 1):
#             c = ws.cell(r, col)
#             c.font   = Font(bold=True)
#             c.fill   = PatternFill("solid", fgColor=total_fill)
#             c.border = border
#             if col > 4:
#                 c.number_format = "0.00%" if col == ncols else '#,##0.00'

#     row_no         = header_row + 1
#     block_start    = row_no
#     current_tso    = None
#     current_region = None

#     for row in data:
#         tso = row.get("tso_name")

#         # TSO changed -> close the previous TSO with a total row
#         if current_tso is not None and tso != current_tso:
#             write_tso_total(row_no, current_tso, current_region, block_start, row_no - 1)
#             row_no += 1
#             block_start = row_no

#         current_tso    = tso
#         current_region = row.get("custom_region")

#         values = [row.get("custom_region"), tso, row.get("customer_name"), row.get("customer_group")]
#         for cat in categories:
#             safe = safe_field(cat)
#             values.append(flt(row.get(f"{safe}_target")))
#             values.append(flt(row.get(f"{safe}_achieved")))

#         total_target   = flt(row.get("total_target"))
#         total_achieved = flt(row.get("total_achieved"))
#         ach_percent    = total_achieved / total_target if total_target else 0
#         values        += [total_target, total_achieved, ach_percent]

#         for col, value in enumerate(values, 1):
#             cell           = ws.cell(row_no, col)
#             cell.value     = value
#             cell.border    = border
#             cell.alignment = Alignment(vertical="center", wrap_text=True)
#             if col > 4:
#                 cell.number_format = '#,##0.00'
#             if 5 <= col <= ncols - 3:
#                 cell.fill = PatternFill("solid", fgColor=yellow if (col - 5) % 2 == 0 else blue)
#             if col == ncols:
#                 cell.number_format = "0.00%"

#         row_no += 1

#     # close the last TSO
#     if current_tso is not None:
#         write_tso_total(row_no, current_tso, current_region, block_start, row_no - 1)
#         row_no += 1

#     # Grand Total adds only the TSO TOTAL rows (no double counting)
#     total_row = row_no
#     last_data = total_row - 1
#     ws.cell(total_row, 1).value = "Grand Total"
#     for col in range(5, ncols):
#         L = get_column_letter(col)
#         ws.cell(total_row, col).value = (
#             f'=SUMIF($C${header_row+1}:$C${last_data},"TOTAL*",{L}{header_row+1}:{L}{last_data})'
#         )
#     ws.cell(total_row, ncols).value = f"=IF({tt_col}{total_row}=0,0,{ta_col}{total_row}/{tt_col}{total_row})"
#     for col in range(1, ncols + 1):
#         c = ws.cell(total_row, col)
#         c.font   = Font(bold=True)
#         c.fill   = PatternFill("solid", fgColor="B6D7A8")
#         c.border = border
#         if col > 4:
#             c.number_format = "0.00%" if col == ncols else '#,##0.00'

#     ws.freeze_panes = f"E{header_row+1}"
#     ws.auto_filter.ref = f"A{header_row}:{get_column_letter(ncols)}{total_row-1}"
#     ws.column_dimensions["A"].width = 14
#     ws.column_dimensions["B"].width = 24
#     ws.column_dimensions["C"].width = 35
#     ws.column_dimensions["D"].width = 22
#     for col in range(5, ncols + 1):
#         ws.column_dimensions[get_column_letter(col)].width = 14


# def make_region_summary_sheet(ws, data,
#                                sheet_label="Region Summary",
#                                period_label=None):
#     dark_green  = "0B6A57"
#     period_fill = "E8F5F1"
#     thin        = Side(style="thin", color="999999")
#     border      = Border(left=thin, right=thin, top=thin, bottom=thin)
#     headers     = ["Region", "Target", "Achieved", "Gap", "Achievement %"]

#     ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
#     title           = ws.cell(1, 1)
#     title.value     = f"Vinod Cookware — {sheet_label}"
#     title.font      = Font(bold=True, color="FFFFFF", size=12)
#     title.fill      = PatternFill("solid", fgColor=dark_green)
#     title.alignment = Alignment(horizontal="center")

#     ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
#     period_cell           = ws.cell(2, 1)
#     period_cell.value     = f"Period: {period_label}" if period_label else "Period: All Data"
#     period_cell.font      = Font(bold=True, color="0B3D5C", size=10)
#     period_cell.fill      = PatternFill("solid", fgColor=period_fill)
#     period_cell.alignment = Alignment(horizontal="center")

#     header_row = 3
#     for col, h in enumerate(headers, 1):
#         cell           = ws.cell(header_row, col)
#         cell.value     = h
#         cell.font      = Font(bold=True, color="FFFFFF")
#         cell.fill      = PatternFill("solid", fgColor=dark_green)
#         cell.border    = border
#         cell.alignment = Alignment(horizontal="center")

#     row_no = header_row + 1
#     for row in get_region_summary_data(data):
#         ws.cell(row_no, 1).value = row["region"]
#         ws.cell(row_no, 2).value = row["target"]
#         ws.cell(row_no, 3).value = row["achieved"]
#         ws.cell(row_no, 4).value = row["gap"]
#         ws.cell(row_no, 5).value = row["achievement_percent"] / 100
#         for col in range(1, 6):
#             c = ws.cell(row_no, col)
#             c.border = border
#             if col in [2, 3, 4]:
#                 c.number_format = '#,##0.00'
#             if col == 5:
#                 c.number_format = "0.00%"
#         row_no += 1

#     for col in range(1, 6):
#         ws.column_dimensions[get_column_letter(col)].width = 18


# def add_region_chart(ws, header_row=1):
#     if ws.max_row < header_row + 1:
#         return

#     chart         = BarChart()
#     chart.title   = "Region — Target vs Achieved"
#     chart.y_axis.title = "Amount"
#     chart.x_axis.title = "Region"

#     data_ref = Reference(ws, min_col=2, max_col=3,
#                          min_row=header_row, max_row=ws.max_row)
#     cats_ref = Reference(ws, min_col=1,
#                          min_row=header_row + 1, max_row=ws.max_row)

#     chart.add_data(data_ref, titles_from_data=True)
#     chart.set_categories(cats_ref)
#     chart.height = 10
#     chart.width  = 20

#     anchor_row = header_row - 1 if header_row > 1 else 2
#     ws.add_chart(chart, f"G{anchor_row}")


# @frappe.whitelist()
# def get_mis_dashboard_data(from_date=None, to_date=None, customer_group=None):
#     filters = frappe._dict({
#         "from_date":      from_date,
#         "to_date":        to_date,
#         "customer_group": customer_group or "Debtors Distributors"
#     })

#     categories = get_categories(filters)
#     data       = get_data(filters, categories)

#     total_target   = sum(flt(d.get("total_target"))   for d in data)
#     total_achieved = sum(flt(d.get("total_achieved")) for d in data)
#     total_gap      = total_target - total_achieved
#     total_achievement = (
#         total_achieved / total_target * 100 if total_target else 0
#     )

#     category_summary = []
#     for cat in categories:
#         safe     = safe_field(cat)
#         target   = sum(flt(d.get(f"{safe}_target"))   for d in data)
#         achieved = sum(flt(d.get(f"{safe}_achieved")) for d in data)
#         gap      = target - achieved
#         category_summary.append({
#             "category":    cat,
#             "target":      target,
#             "achieved":    achieved,
#             "gap":         gap,
#             "achievement": achieved / target * 100 if target else 0
#         })

#     # >>> CHANGED: skip display-only categories that are already real columns now
#     existing = {normalize(c) for c in categories}
#     for cat in DISPLAY_ONLY_CATEGORIES:
#         if normalize(cat) in existing:
#             continue
#         achieved = get_display_only_category_totals(filters, cat)
#         category_summary.append({
#             "category":    cat,
#             "target":      0,
#             "achieved":    achieved,
#             "achievement": 0
#         })

#     AREA_FIELD_MAP = {
#         "ROM":       (["parent_sales_person"], ["Sandeep Kumar"]),
#         "Mumbai AH": (["parent_sales_person"], ["Muslim Abdulla Hakim (Aslam)"]),
#         "Gujarat":   (["tso_name", "parent_sales_person"], ["MAYUR TALATI"]),
#         "MPCG":      (["parent_sales_person", "tso_name"], ["Jaydeo Deshmukh"]),
#     }

#     AREA_MAP = {
#         "North":     lambda r: r.get("custom_region") == "North",
#         "South":     lambda r: r.get("custom_region") == "South",
#         "East":      lambda r: r.get("custom_region") == "East",
#         "ROM":       lambda r: row_matches_section(r, *AREA_FIELD_MAP["ROM"]),
#         "Mumbai AH": lambda r: row_matches_section(r, *AREA_FIELD_MAP["Mumbai AH"]),
#         "Gujarat":   lambda r: row_matches_section(r, *AREA_FIELD_MAP["Gujarat"]),
#         "MPCG":      lambda r: row_matches_section(r, *AREA_FIELD_MAP["MPCG"]),
#     }

#     area_summary = []
#     for area, condition in AREA_MAP.items():
#         rows     = [x for x in data if condition(x)]
#         target   = sum(flt(r.get("total_target"))   for r in rows)
#         achieved = sum(flt(r.get("total_achieved")) for r in rows)
#         gap      = target - achieved
#         area_summary.append({
#             "area":        area,
#             "target":      target,
#             "achieved":    achieved,
#             "gap":         gap,
#             "achievement": achieved / target * 100 if target else 0
#         })

#     # real category totals for each region
#     region_category = {}
#     for area, condition in AREA_MAP.items():
#         area_rows = [x for x in data if condition(x)]
#         region_category[area] = []
#         for cat in categories:
#             safe = safe_field(cat)
#             t = sum(flt(r.get(f"{safe}_target"))   for r in area_rows)
#             a = sum(flt(r.get(f"{safe}_achieved")) for r in area_rows)
#             region_category[area].append({
#                 "category":    cat,
#                 "target":      t,
#                 "achieved":    a,
#                 "gap":         t - a,
#                 "achievement": a / t * 100 if t else 0
#             })

#     return {
#         "kpi": {
#             "target":      total_target,
#             "achieved":    total_achieved,
#             "gap":         total_gap,
#             "achievement": total_achievement
#         },
#         "category_summary": category_summary,
#         "area_summary":     area_summary,
#         "region_category":  region_category
#     }


# Copyright (c) 2026, Sukku and contributors
# For license information, please see license.txt
#
# CUSTOMER GROUP REPORT  =  exact copy of TEST REPORT.
#
# The ONLY differences (all marked with  # >>> CHANGED) are the ones needed so that
# no Sales Invoice value is dropped, so figures match "Sales Analytic Dashboard":
#   1. Items with a blank Main Group are no longer removed          -> shown as "Unmapped"
#   2. Main Groups that are not in the category list are no longer ignored
#      -> they get their own column automatically
#   3. LEFT JOIN on Item / Customer (INNER JOIN used to drop lines)
#   4. Total Achieved counts every category (the "target > 0" rule for
#      Debtors Distributors is removed - it hid sales from the Total)
#   5. Opening invoices (is_opening = 'Yes') are excluded, same as Sales Analytics
#   6. Excel export: sub-total rows are now CUSTOMER-wise ("TOTAL — <customer>")
#      instead of TSO-wise ("TOTAL — <TSO>")

import io
import frappe
from frappe import _
from frappe.utils import flt, getdate

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_FIELD_MAP = {
    1: "jan_target", 2: "feb_target", 3: "mar_target",
    4: "apr_target", 5: "may_target", 6: "jun_target",
    7: "jul_target", 8: "aug_target", 9: "sep_target",
    10: "oct_target", 11: "nov_target", 12: "dec_target"
}

DEFAULT_CATEGORIES = [
    "Nonstick",
    "Horeca",
    "Pressure Cookers",
    "SS Cookware",
    "Healux",
    "Kraft",
    "Platinum",
    "Platinum Triply P.cooker",
    "Cast Iron",
    "Bottle",
    "Csd",
    "Other",
    "Futuretec"
]

DISPLAY_ONLY_CATEGORIES = [
    "Freya Cast Iron",
]

# >>> CHANGED: bucket for items that have no Main Group
UNMAPPED = "Unmapped"
CAT_EXPR = "COALESCE(NULLIF(TRIM(i.custom_main_group), ''), 'Unmapped')"

SECTION_VIEW_MAP = {
    "North Detail":      (["parent_sales_person"], ["Rajiv K Dutta"]),
    "East Detail":       (["parent_sales_person"], ["Pannalal Bhattacharya"]),
    "South Detail":      (["parent_sales_person"], ["Mohammed Muqeemudheen Cherayakkuth"]),
    "ROM Detail":        (["parent_sales_person"], ["Sandeep Kumar"]),
    "MPCG Detail":       (["parent_sales_person", "tso_name"], ["Jaydeo Deshmukh"]),
    "Mumbai AH Detail":  (["parent_sales_person"], ["Muslim Abdulla Hakim (Aslam)"]),
    "Gujarat Detail":    (["tso_name", "parent_sales_person"], ["MAYUR TALATI"]),
}

_target_cache = {}


def safe_field(category):
    # >>> CHANGED: also strip / & ( ) so newly found category names stay valid field names
    return (
        category.replace(" ", "_").replace("-", "_")
        .replace("/", "_").replace("&", "_").replace("(", "_").replace(")", "_")
    )


def normalize(value):
    return (value or "").strip().casefold()


def row_matches_section(row, fieldnames, selected_values):
    normalized_targets = {normalize(v) for v in selected_values}
    for fieldname in fieldnames:
        if normalize(row.get(fieldname)) in normalized_targets:
            return True
    return False


def filter_section_rows(rows, fieldnames, selected_values):
    return [r for r in rows if row_matches_section(r, fieldnames, selected_values)]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date must be before To Date"))

    categories = get_categories(filters)
    raw_data   = get_data(filters, categories)
    view_type  = filters.get("view_type") or "TSO Summary"

    if view_type == "Region Summary":
        columns = get_region_summary_columns()
        data    = get_region_summary_data(raw_data)

    elif view_type in SECTION_VIEW_MAP:
        fieldnames, selected_values = SECTION_VIEW_MAP[view_type]
        columns = get_columns(categories, filters)
        data    = filter_section_rows(raw_data, fieldnames, selected_values)

    else:
        columns = get_columns(categories, filters)
        data    = raw_data

    return columns, data


def parse_multi(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [x.strip() for x in str(value).split(",") if x.strip()]


def get_customer_group_list(customer_group):
    """Selected group + every child group under it (Customer Group is a tree)."""
    if not customer_group:
        return []
    vals = frappe.db.get_value("Customer Group", customer_group, ["lft", "rgt"])
    if not vals:
        return [customer_group]
    lft, rgt = vals
    names = frappe.get_all(
        "Customer Group",
        filters={"lft": [">=", lft], "rgt": ["<=", rgt]},
        pluck="name"
    )
    return names or [customer_group]


# >>> CHANGED: category list = the ones in the filter / defaults (same as Test Report)
#              PLUS every other Main Group that really has sales in the period
#              PLUS "Unmapped" when some items have no Main Group.
def get_extra_categories(filters):
    conditions = ["si.docstatus = 1", "IFNULL(si.is_opening, 'No') = 'No'"]
    values     = {}

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("customer_group"):
        conditions.append("si.customer_group IN %(customer_group)s")
        values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

    rows = frappe.db.sql(f"""
        SELECT DISTINCT {CAT_EXPR} AS category
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabItem` i ON i.name = sii.item_code
        WHERE {" AND ".join(conditions)}
    """, values, as_dict=1)

    found = sorted({r.category for r in rows if r.category and r.category != UNMAPPED},
                   key=lambda x: x.casefold())
    if any(r.category == UNMAPPED for r in rows):
        found.append(UNMAPPED)
    return found


def get_categories(filters):
    if filters.get("custom_main_group"):
        if isinstance(filters.custom_main_group, list):
            base = list(filters.custom_main_group)
        else:
            base = [x.strip() for x in str(filters.custom_main_group).split(",") if x.strip()]
    else:
        base = list(DEFAULT_CATEGORIES)

    seen = {normalize(c) for c in base}
    for cat in get_extra_categories(filters):
        if normalize(cat) not in seen:
            base.append(cat)
            seen.add(normalize(cat))
    return base


def get_columns(categories, filters=None):
    columns = []

    if filters and filters.get("show_item_details"):
        columns.extend([
            {"label": _("Item Code"), "fieldname": "item_code",
             "fieldtype": "Link", "options": "Item", "width": 150},
            {"label": _("Item Name"), "fieldname": "item_name",
             "fieldtype": "Data", "width": 200}
        ])

    columns.extend([
        {"label": _("Month"),            "fieldname": "month",               "fieldtype": "Data",     "width": 100},
        {"label": _("TSO"),              "fieldname": "tso_name",            "fieldtype": "Data",     "width": 200},
        {"label": _("Customer Name"),    "fieldname": "customer_name",       "fieldtype": "Data",     "width": 220},
        {"label": _("Customer Group"),   "fieldname": "customer_group",      "fieldtype": "Data",     "width": 200},
        {"label": _("Region"),           "fieldname": "custom_region",       "fieldtype": "Data",     "width": 130},
        {"label": _("Territory Code"),   "fieldname": "custom_territory",    "fieldtype": "Data",     "width": 130},
        {"label": _("Head Sales Person"),"fieldname": "parent_sales_person", "fieldtype": "Data",     "width": 200},
        {"label": _("Total Achieved"),   "fieldname": "total_achieved",      "fieldtype": "Currency", "width": 150},
        {"label": _("Total Target"),     "fieldname": "total_target",        "fieldtype": "Currency", "width": 150},
        {"label": _("Achievement %"),    "fieldname": "achievement_percent", "fieldtype": "Percent",  "width": 120},
    ])

    for cat in categories:
        safe = safe_field(cat)
        columns.append({"label": _(f"{cat} Target"),   "fieldname": f"{safe}_target",
                         "fieldtype": "Currency", "width": 130})
        columns.append({"label": _(f"{cat} Achieved"), "fieldname": f"{safe}_achieved",
                         "fieldtype": "Currency", "width": 130})

    return columns


def get_region_summary_columns():
    return [
        {"label": _("Region"),         "fieldname": "region",              "fieldtype": "Data",     "width": 180},
        {"label": _("Target"),         "fieldname": "target",              "fieldtype": "Currency", "width": 150},
        {"label": _("Achieved"),       "fieldname": "achieved",            "fieldtype": "Currency", "width": 150},
        {"label": _("Gap"),            "fieldname": "gap",                 "fieldtype": "Currency", "width": 150},
        {"label": _("Achievement %"),  "fieldname": "achievement_percent", "fieldtype": "Percent",  "width": 120},
    ]


def _load_targets_for_customer(customer, month_num):
    cache_key = (customer, month_num)
    if cache_key in _target_cache:
        return _target_cache[cache_key]

    month_field = MONTH_FIELD_MAP.get(int(month_num), "jan_target")

    try:
        rows = frappe.db.sql(f"""
            SELECT
                mtd.main_group,
                mtd.{month_field} AS target_amount
            FROM `tabMonthly Target Detail` mtd
            INNER JOIN `tabSales Person Target` spt
                ON spt.name = mtd.parent
            WHERE spt.name        = %(customer)s
              AND spt.period_type = 'Monthly'
              AND spt.docstatus   IN (0, 1)
        """, {"customer": customer}, as_dict=1)

        result = {r.main_group: flt(r.target_amount) for r in rows if r.main_group}
        _target_cache[cache_key] = result
        return result

    except Exception as e:
        frappe.log_error(f"Target fetch error for customer {customer}: {e}", "CUSTOMER GROUP REPORT")

    _target_cache[cache_key] = {}
    return {}


def get_target_for_customer_category(customer, month_num, category):
    targets = _load_targets_for_customer(customer, month_num)
    return flt(targets.get(category, 0))


def get_display_only_category_totals(filters, category):
    conditions = ["si.docstatus = 1", "i.custom_main_group = %(category)s"]
    values     = {"category": category}

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    if filters.get("customer_group"):
        conditions.append("si.customer_group IN %(customer_group)s")
        values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

    where_clause = " AND ".join(conditions)

    row = frappe.db.sql(f"""
        SELECT COALESCE(SUM(sii.base_net_amount), 0) AS achieved
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        INNER JOIN `tabItem` i ON i.name = sii.item_code
        WHERE {where_clause}
    """, values, as_dict=1)

    return flt(row[0].achieved) if row else 0


def get_achieved_data(filters, categories):
    global _target_cache
    _target_cache = {}

    # >>> CHANGED: opening invoices excluded (same as Sales Analytics dashboard)
    conditions = ["si.docstatus = 1", "IFNULL(si.is_opening, 'No') = 'No'"]
    values     = {}

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    # filter uses sp_cust only (Customer master TSO)
    if filters.get("sales_person"):
        conditions.append("sp_cust.name = %(sales_person)s")
        values["sales_person"] = filters.get("sales_person")

    if filters.get("parent_sales_person"):
        conditions.append("sp_cust.parent_sales_person = %(parent_sales_person)s")
        values["parent_sales_person"] = filters.get("parent_sales_person")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("customer_group"):
        conditions.append("si.customer_group IN %(customer_group)s")
        values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

    regions = parse_multi(filters.get("custom_region"))
    if regions:
        conditions.append("sp_cust.custom_region IN %(custom_region)s")
        values["custom_region"] = tuple(regions)

    territories = parse_multi(filters.get("custom_territory"))
    if territories:
        conditions.append("sp_cust.custom_territory IN %(custom_territory)s")
        values["custom_territory"] = tuple(territories)

    codes = parse_multi(filters.get("custom_head_sales_code"))
    if codes:
        conditions.append("sp_cust.custom_head_sales_code IN %(custom_head_sales_code)s")
        values["custom_head_sales_code"] = tuple(codes)

    # >>> CHANGED: the Category filter no longer removes sales in SQL.
    #     It only decides which columns are shown first; every other category
    #     is added as an extra column, so nothing is lost from the Total.

    where_clause = " AND ".join(conditions)

    group_by = f"""
        DATE_FORMAT(si.posting_date, '%%Y-%%m'),
        MONTH(si.posting_date),
        YEAR(si.posting_date),
        si.customer,
        si.customer_group,
        sp_cust.name,
        sp_cust.parent_sales_person,
        sp_cust.custom_region,
        sp_cust.custom_territory,
        sp_cust.custom_head_sales_code,
        c.customer_name,
        {CAT_EXPR}
    """

    if filters.get("show_item_details"):
        item_cols = "sii.item_code AS item_code, i.item_name AS item_name,"
        group_by += ", sii.item_code, i.item_name"
    else:
        item_cols = "'' AS item_code, '' AS item_name,"

    # >>> CHANGED: LEFT JOIN Item / Customer, no custom_main_group IS NOT NULL / != '' filter
    query = f"""
        SELECT
            DATE_FORMAT(si.posting_date, '%%Y-%%m')  AS month_key,
            MONTH(si.posting_date)                    AS month_num,
            YEAR(si.posting_date)                     AS year,
            si.customer                               AS customer,
            si.customer_group                         AS customer_group,
            COALESCE(sp_cust.name, 'Unassigned')      AS tso_name,
            COALESCE(sp_cust.parent_sales_person, '')  AS parent_sales_person,
            COALESCE(sp_cust.custom_region, '')        AS custom_region,
            COALESCE(sp_cust.custom_territory, '')     AS custom_territory,
            COALESCE(sp_cust.custom_head_sales_code, '') AS custom_head_sales_code,
            c.customer_name                           AS customer_name,
            {CAT_EXPR}                                AS category,
            {item_cols}
            SUM(sii.base_net_amount)                  AS achieved,
            COUNT(DISTINCT si.name)                   AS invoice_count,
            COUNT(DISTINCT sii.item_code)             AS item_count
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name
        LEFT JOIN `tabItem` i
            ON i.name = sii.item_code
        LEFT JOIN `tabCustomer` c
            ON c.name = si.customer

        -- ONLY Customer master Sales Team, idx=1 to prevent duplicates
        LEFT JOIN `tabSales Team` st_cust
            ON st_cust.parent      = si.customer
            AND st_cust.parenttype = 'Customer'
            AND st_cust.idx        = 1

        LEFT JOIN `tabSales Person` sp_cust
            ON sp_cust.name = st_cust.sales_person

        WHERE {where_clause}
        GROUP BY {group_by}
        ORDER BY
            YEAR(si.posting_date),
            MONTH(si.posting_date),
            sp_cust.custom_region,
            sp_cust.name,
            c.customer_name
    """

    rows       = frappe.db.sql(query, values, as_dict=1)
    result     = {}
    cat_lookup = {normalize(c): c for c in categories}

    for row in rows:
        tso      = row.tso_name or "Unassigned"
        customer = row.customer

        # >>> CHANGED: customer_group added to the key so a customer's invoices
        #     that carry different groups are never merged into the wrong group
        if filters.get("show_item_details"):
            key = (row.month_key, customer, tso, row.customer_group, row.item_code)
        else:
            key = (row.month_key, customer, tso, row.customer_group)

        if key not in result:
            entry = {
                "customer":            customer,
                "customer_group":      row.customer_group or "",
                "month":               f"{MONTHS[int(row.month_num)-1]}-{row.year}",
                "month_num":           row.month_num,
                "year":                row.year,
                "tso_name":            tso,
                "customer_name":       row.customer_name or "No Customer",
                "parent_sales_person": row.parent_sales_person or "",
                "custom_region":       row.custom_region or "",
                "custom_territory":    row.custom_territory or "",
                "custom_head_sales_code": row.custom_head_sales_code or "",
                "total_achieved":      0,
                "total_target":        0,
                "achievement_percent": 0,
                "invoice_count":       0,
                "item_count":          0
            }

            if filters.get("show_item_details"):
                entry["item_code"] = row.item_code
                entry["item_name"] = row.item_name

            for cat in categories:
                safe = safe_field(cat)
                entry[f"{safe}_achieved"] = 0
                target_value = get_target_for_customer_category(
                    customer, row.month_num, cat
                )
                entry[f"{safe}_target"]  = flt(target_value)
                entry["total_target"]   += flt(target_value)

            result[key] = entry

        cat = cat_lookup.get(normalize(row.category))
        if cat:
            safe              = safe_field(cat)
            category_achieved = flt(row.achieved)

            result[key][f"{safe}_achieved"] += category_achieved

            # >>> CHANGED: every category counts toward Total Achieved
            result[key]["total_achieved"] += category_achieved
            result[key]["invoice_count"]  += int(row.invoice_count or 0)
            result[key]["item_count"]     += int(row.item_count or 0)

    return list(result.values())


def get_month_year_range(from_date, to_date):
    start = getdate(from_date)
    end   = getdate(to_date)
    result = []
    y, m = start.year, start.month

    while (y, m) <= (end.year, end.month):
        result.append((y, m))
        if m == 12:
            y += 1
            m  = 1
        else:
            m += 1

    return result


def get_target_skeleton_rows(filters, categories, month_year_list):
    if not categories or not month_year_list:
        return []

    conditions = ["spt.period_type = 'Monthly'", "spt.docstatus IN (0, 1)"]
    values     = {"categories": tuple(categories)}
    conditions.append("mtd.main_group IN %(categories)s")

    if filters.get("customer"):
        conditions.append("spt.name = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("customer_group"):
        conditions.append("c.customer_group IN %(customer_group)s")
        values["customer_group"] = tuple(get_customer_group_list(filters.get("customer_group")))

    regions = parse_multi(filters.get("custom_region"))
    if regions:
        conditions.append("sp_cust.custom_region IN %(custom_region)s")
        values["custom_region"] = tuple(regions)

    territories = parse_multi(filters.get("custom_territory"))
    if territories:
        conditions.append("sp_cust.custom_territory IN %(custom_territory)s")
        values["custom_territory"] = tuple(territories)

    codes = parse_multi(filters.get("custom_head_sales_code"))
    if codes:
        conditions.append("sp_cust.custom_head_sales_code IN %(custom_head_sales_code)s")
        values["custom_head_sales_code"] = tuple(codes)

    if filters.get("sales_person"):
        conditions.append("sp_cust.name = %(sales_person)s")
        values["sales_person"] = filters.get("sales_person")

    if filters.get("parent_sales_person"):
        conditions.append("sp_cust.parent_sales_person = %(parent_sales_person)s")
        values["parent_sales_person"] = filters.get("parent_sales_person")

    where_clause    = " AND ".join(conditions)
    month_field_cols = ", ".join(f"mtd.{f}" for f in MONTH_FIELD_MAP.values())

    rows = frappe.db.sql(f"""
        SELECT
            spt.name                                    AS customer,
            c.customer_name                             AS customer_name,
            c.customer_group                            AS customer_group,
            mtd.main_group                              AS category,
            {month_field_cols},
            COALESCE(sp_cust.name, 'Unassigned')        AS tso_name,
            COALESCE(sp_cust.parent_sales_person, '')    AS parent_sales_person,
            COALESCE(sp_cust.custom_region, '')          AS custom_region,
            COALESCE(sp_cust.custom_territory, '')       AS custom_territory,
            COALESCE(sp_cust.custom_head_sales_code, '') AS custom_head_sales_code
        FROM `tabSales Person Target` spt
        INNER JOIN `tabMonthly Target Detail` mtd
            ON mtd.parent = spt.name
        INNER JOIN `tabCustomer` c
            ON c.name = spt.name
        LEFT JOIN `tabSales Team` st_cust
            ON st_cust.parent      = c.name
            AND st_cust.parenttype = 'Customer'
            AND st_cust.idx        = 1
        LEFT JOIN `tabSales Person` sp_cust
            ON sp_cust.name = st_cust.sales_person
        WHERE {where_clause}
    """, values, as_dict=1)

    by_customer = {}
    for r in rows:
        info = by_customer.setdefault(r.customer, {
            "customer_name":          r.customer_name or "No Customer",
            "customer_group":         r.customer_group or "",
            "tso_name":               r.tso_name,
            "parent_sales_person":    r.parent_sales_person,
            "custom_region":          r.custom_region,
            "custom_territory":       r.custom_territory,
            "custom_head_sales_code": r.custom_head_sales_code,
            "categories":             {}
        })
        info["categories"][r.category] = r

    skeleton = {}

    for customer, info in by_customer.items():
        for year, month in month_year_list:
            month_key   = f"{year:04d}-{month:02d}"
            month_field = MONTH_FIELD_MAP[month]
            key         = (month_key, customer, info["tso_name"])

            if key not in skeleton:
                entry = {
                    "customer":               customer,
                    "month":                  f"{MONTHS[month-1]}-{year}",
                    "month_num":              month,
                    "year":                   year,
                    "tso_name":               info["tso_name"],
                    "customer_name":          info["customer_name"],
                    "customer_group":         info["customer_group"],
                    "parent_sales_person":    info["parent_sales_person"],
                    "custom_region":          info["custom_region"],
                    "custom_territory":       info["custom_territory"],
                    "custom_head_sales_code": info["custom_head_sales_code"],
                    "total_achieved":         0,
                    "total_target":           0,
                    "achievement_percent":    0,
                    "invoice_count":          0,
                    "item_count":             0
                }

                if filters.get("show_item_details"):
                    entry["item_code"] = ""
                    entry["item_name"] = ""

                for cat in categories:
                    safe = safe_field(cat)
                    entry[f"{safe}_achieved"] = 0
                    entry[f"{safe}_target"]   = 0

                skeleton[key] = entry

            entry = skeleton[key]

            for cat in categories:
                cat_row = info["categories"].get(cat)
                if not cat_row:
                    continue
                target_amt = flt(cat_row.get(month_field))
                if target_amt:
                    safe = safe_field(cat)
                    entry[f"{safe}_target"] += target_amt
                    entry["total_target"]   += target_amt

    return list(skeleton.values())


def get_data(filters, categories):
    final_data = get_achieved_data(filters, categories)

    from_date = filters.get("from_date")
    to_date   = filters.get("to_date")

    if from_date and to_date:
        covered_customer_months = set()
        for row in final_data:
            covered_customer_months.add((
                f'{int(row.get("year")):04d}-{int(row.get("month_num")):02d}',
                row.get("customer")
            ))

        month_year_list = get_month_year_range(from_date, to_date)
        skeleton_rows   = get_target_skeleton_rows(filters, categories, month_year_list)

        for srow in skeleton_rows:
            skey = (
                f'{int(srow.get("year")):04d}-{int(srow.get("month_num")):02d}',
                srow.get("customer")
            )
            if skey not in covered_customer_months and flt(srow.get("total_target")) > 0:
                final_data.append(srow)

    for row in final_data:
        row["achievement_percent"] = (
            flt(row.get("total_achieved")) / flt(row.get("total_target")) * 100
            if flt(row.get("total_target")) else 0
        )

    return final_data


def get_region_bucket(row):
    region = (row.get("custom_region") or "").strip()

    if region in ("North", "South", "East"):
        return region

    if row_matches_section(row, *SECTION_VIEW_MAP["ROM Detail"]):
        return "ROM"
    if row_matches_section(row, *SECTION_VIEW_MAP["Mumbai AH Detail"]):
        return "Mumbai AH"
    if row_matches_section(row, *SECTION_VIEW_MAP["MPCG Detail"]):
        return "MPCG"
    if row_matches_section(row, *SECTION_VIEW_MAP["Gujarat Detail"]):
        return "Gujarat"

    return region or "Unassigned"


def get_region_summary_data(data):
    result = {}

    for row in data:
        region = get_region_bucket(row)

        if region not in result:
            result[region] = {
                "region":  region,
                "target":  0,
                "achieved": 0,
                "gap":     0,
                "achievement_percent": 0
            }

        result[region]["target"]   += flt(row.get("total_target"))
        result[region]["achieved"] += flt(row.get("total_achieved"))

    final = []
    for region, row in result.items():
        row["gap"] = row["target"] - row["achieved"]
        row["achievement_percent"] = (
            row["achieved"] / row["target"] * 100
            if row["target"] else 0
        )
        final.append(row)

    return sorted(final, key=lambda x: x["region"])


def aggregate_party_wise(data, categories):
    grouped = {}

    for row in data:
        # >>> CHANGED: customer_group added to the key (see get_achieved_data)
        key = (row.get("customer"), row.get("tso_name"), row.get("customer_group"))

        if key not in grouped:
            entry = {
                "customer":               row.get("customer"),
                "customer_name":          row.get("customer_name"),
                "customer_group":         row.get("customer_group"),
                "tso_name":               row.get("tso_name"),
                "parent_sales_person":    row.get("parent_sales_person"),
                "custom_region":          row.get("custom_region"),
                "custom_territory":       row.get("custom_territory"),
                "custom_head_sales_code": row.get("custom_head_sales_code"),
                "month":                  "All",
                "total_achieved":         0,
                "total_target":           0,
                "achievement_percent":    0,
                "invoice_count":          0,
                "item_count":             0
            }
            for cat in categories:
                safe = safe_field(cat)
                entry[f"{safe}_target"]   = 0
                entry[f"{safe}_achieved"] = 0

            grouped[key] = entry

        entry = grouped[key]
        entry["total_achieved"] += flt(row.get("total_achieved"))
        entry["total_target"]   += flt(row.get("total_target"))
        entry["invoice_count"]  += flt(row.get("invoice_count"))
        entry["item_count"]     += flt(row.get("item_count"))

        for cat in categories:
            safe = safe_field(cat)
            entry[f"{safe}_target"]   += flt(row.get(f"{safe}_target"))
            entry[f"{safe}_achieved"] += flt(row.get(f"{safe}_achieved"))

    result = list(grouped.values())
    for entry in result:
        entry["achievement_percent"] = (
            entry["total_achieved"] / entry["total_target"] * 100
            if entry["total_target"] else 0
        )

    return result


def get_summary(data, categories):
    total_achieved = total_target = total_invoice = total_item = 0

    for row in data:
        total_achieved += flt(row.get("total_achieved"))
        total_target   += flt(row.get("total_target"))
        total_invoice  += flt(row.get("invoice_count"))
        total_item     += flt(row.get("item_count"))

    ach_percent = total_achieved / total_target * 100 if total_target else 0

    return [
        {"label": _("Total Achieved"), "value": total_achieved, "indicator": "Green",  "datatype": "Currency"},
        {"label": _("Total Target"),   "value": total_target,   "indicator": "Yellow", "datatype": "Currency"},
        {"label": _("Achievement %"),  "value": ach_percent,    "indicator": "Purple", "datatype": "Percent"},
        {"label": _("Invoice Count"),  "value": total_invoice,  "indicator": "Orange", "datatype": "Int"},
        {"label": _("Item Count"),     "value": total_item,     "indicator": "Grey",   "datatype": "Int"},
    ]


def get_chart(data):
    region_data = get_region_summary_data(data)
    if not region_data:
        return None

    return {
        "data": {
            "labels": [d["region"] for d in region_data],
            "datasets": [
                {"name": "Target",   "values": [d["target"]   for d in region_data]},
                {"name": "Achieved", "values": [d["achieved"] for d in region_data]}
            ]
        },
        "type": "bar",
        "height": 280,
    }


def get_period_label(filters):
    from_date = filters.get("from_date")
    to_date   = filters.get("to_date")
    if not (from_date and to_date):
        return "All Data"
    return f"{frappe.utils.formatdate(from_date)} to {frappe.utils.formatdate(to_date)}"


@frappe.whitelist()
def download_mis_excel(**filters):
    filters      = frappe._dict(filters or {})
    categories   = get_categories(filters)
    data         = get_data(filters, categories)
    view_type    = filters.get("view_type") or "TSO Summary"
    period_label = get_period_label(filters)
    party_wise_total = int(filters.get("party_wise_total") or 0)

    wb = Workbook()

    if view_type == "Region Summary":
        ws = wb.active
        ws.title = "Region Summary"
        make_region_summary_sheet(ws, data, sheet_label="Region Summary", period_label=period_label)
        add_region_chart(ws, header_row=3)
        filename_part = "Region_Summary"

    elif view_type in SECTION_VIEW_MAP:
        fieldnames, selected_values = SECTION_VIEW_MAP[view_type]
        section_rows    = filter_section_rows(data, fieldnames, selected_values)
        clean_sheet_name = view_type.replace(" Detail", "")[:31]
        rows_for_sheet  = (
            aggregate_party_wise(section_rows, categories)
            if party_wise_total else section_rows
        )
        ws = wb.active
        ws.title = clean_sheet_name
        make_tso_summary_sheet(
            ws, rows_for_sheet, categories,
            sheet_label=f"{clean_sheet_name} — Target vs Achievement",
            period_label=period_label
        )
        filename_part = clean_sheet_name.replace(" ", "_")

    else:
        tso_rows = aggregate_party_wise(data, categories) if party_wise_total else data
        ws = wb.active
        ws.title = "TSO Summary"
        make_tso_summary_sheet(
            ws, tso_rows, categories,
            sheet_label="TSO Summary — Target vs Achievement",
            period_label=period_label
        )

        ws_region = wb.create_sheet("Region Summary")
        make_region_summary_sheet(ws_region, data,
                                  sheet_label="Region Summary", period_label=period_label)

        ws_chart = wb.create_sheet("Charts")
        make_region_summary_sheet(ws_chart, data,
                                  sheet_label="Region Summary (Chart)", period_label=period_label)
        add_region_chart(ws_chart, header_row=3)

        for sheet_name, (fieldnames, selected_values) in SECTION_VIEW_MAP.items():
            clean_sheet_name = sheet_name.replace(" Detail", "")[:31]
            section_rows     = filter_section_rows(data, fieldnames, selected_values)
            if section_rows:
                rows_for_sheet = (
                    aggregate_party_wise(section_rows, categories)
                    if party_wise_total else section_rows
                )
                ws_sec = wb.create_sheet(clean_sheet_name)
                make_tso_summary_sheet(
                    ws_sec, rows_for_sheet, categories,
                    sheet_label=f"{clean_sheet_name} — Target vs Achievement",
                    period_label=period_label
                )

        filename_part = "Full_MIS"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    frappe.local.response.filename    = f"Vinod_Cookware_{filename_part}.xlsx"
    frappe.local.response.filecontent = output.read()
    frappe.local.response.type        = "download"


def make_tso_summary_sheet(ws, data, categories,
                            sheet_label="TSO Target vs Achievement",
                            period_label=None):
    dark_green  = "0B6A57"
    yellow      = "FFF2CC"
    blue        = "DDEBF7"
    total_fill  = "D9EAD3"
    period_fill = "E8F5F1"

    thin   = Side(style="thin", color="999999")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers = ["Region", "TSO", "Distributor", "Customer Group"]
    for cat in categories:
        headers.append(f"{cat} Target")
        headers.append(f"{cat} Achieved")
    headers += ["Total Target", "Total Achieved", "Achievement %"]
    ncols = len(headers)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    title = ws.cell(1, 1)
    title.value     = f"Vinod Cookware — {sheet_label}"
    title.font      = Font(bold=True, color="FFFFFF", size=12)
    title.fill      = PatternFill("solid", fgColor=dark_green)
    title.alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    period_cell       = ws.cell(2, 1)
    period_cell.value = f"Period: {period_label}" if period_label else "Period: All Data"
    period_cell.font  = Font(bold=True, color="0B3D5C", size=10)
    period_cell.fill  = PatternFill("solid", fgColor=period_fill)
    period_cell.alignment = Alignment(horizontal="center")

    header_row = 3
    for col, h in enumerate(headers, 1):
        cell           = ws.cell(header_row, col)
        cell.value     = h
        cell.font      = Font(bold=True, color="FFFFFF")
        cell.fill      = PatternFill("solid", fgColor=dark_green)
        cell.border    = border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # >>> CHANGED: sort so each CUSTOMER's rows sit together (region / TSO order kept)
    data = sorted(data, key=lambda r: (
        (r.get("custom_region") or ""),
        (r.get("tso_name") or ""),
        (r.get("customer_name") or ""),
        (r.get("customer") or "")
    ))

    tt_col = get_column_letter(ncols - 2)   # Total Target column letter
    ta_col = get_column_letter(ncols - 1)   # Total Achieved column letter

    # >>> CHANGED: writes one "TOTAL — <Customer>" row (was "TOTAL — <TSO>")
    def write_customer_total(r, customer_name, tso, region, start, end):
        ws.cell(r, 1).value = region
        ws.cell(r, 2).value = tso
        ws.cell(r, 3).value = f"TOTAL — {customer_name}"
        for col in range(5, ncols):
            L = get_column_letter(col)
            ws.cell(r, col).value = f"=SUM({L}{start}:{L}{end})"
        ws.cell(r, ncols).value = f"=IF({tt_col}{r}=0,0,{ta_col}{r}/{tt_col}{r})"
        for col in range(1, ncols + 1):
            c = ws.cell(r, col)
            c.font   = Font(bold=True)
            c.fill   = PatternFill("solid", fgColor=total_fill)
            c.border = border
            if col > 4:
                c.number_format = "0.00%" if col == ncols else '#,##0.00'

    row_no               = header_row + 1
    block_start          = row_no
    current_customer     = None     # customer id (block key)
    current_customer_name = None
    current_tso          = None
    current_region       = None

    for row in data:
        tso      = row.get("tso_name")
        cust_key = row.get("customer") or row.get("customer_name")

        # >>> CHANGED: customer changed -> close the previous customer with a total row
        if current_customer is not None and cust_key != current_customer:
            write_customer_total(row_no, current_customer_name, current_tso,
                                 current_region, block_start, row_no - 1)
            row_no += 1
            block_start = row_no

        current_customer      = cust_key
        current_customer_name = row.get("customer_name")
        current_tso           = tso
        current_region        = row.get("custom_region")

        values = [row.get("custom_region"), tso, row.get("customer_name"), row.get("customer_group")]
        for cat in categories:
            safe = safe_field(cat)
            values.append(flt(row.get(f"{safe}_target")))
            values.append(flt(row.get(f"{safe}_achieved")))

        total_target   = flt(row.get("total_target"))
        total_achieved = flt(row.get("total_achieved"))
        ach_percent    = total_achieved / total_target if total_target else 0
        values        += [total_target, total_achieved, ach_percent]

        for col, value in enumerate(values, 1):
            cell           = ws.cell(row_no, col)
            cell.value     = value
            cell.border    = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if col > 4:
                cell.number_format = '#,##0.00'
            if 5 <= col <= ncols - 3:
                cell.fill = PatternFill("solid", fgColor=yellow if (col - 5) % 2 == 0 else blue)
            if col == ncols:
                cell.number_format = "0.00%"

        row_no += 1

    # >>> CHANGED: close the last customer
    if current_customer is not None:
        write_customer_total(row_no, current_customer_name, current_tso,
                             current_region, block_start, row_no - 1)
        row_no += 1

    # Grand Total adds only the customer TOTAL rows (no double counting)
    total_row = row_no
    last_data = total_row - 1
    ws.cell(total_row, 1).value = "Grand Total"
    for col in range(5, ncols):
        L = get_column_letter(col)
        # >>> CHANGED: criteria "TOTAL — *" so a customer whose name starts with
        #     "Total..." can never be picked up by mistake
        ws.cell(total_row, col).value = (
            f'=SUMIF($C${header_row+1}:$C${last_data},"TOTAL — *",{L}{header_row+1}:{L}{last_data})'
        )
    ws.cell(total_row, ncols).value = f"=IF({tt_col}{total_row}=0,0,{ta_col}{total_row}/{tt_col}{total_row})"
    for col in range(1, ncols + 1):
        c = ws.cell(total_row, col)
        c.font   = Font(bold=True)
        c.fill   = PatternFill("solid", fgColor="B6D7A8")
        c.border = border
        if col > 4:
            c.number_format = "0.00%" if col == ncols else '#,##0.00'

    ws.freeze_panes = f"E{header_row+1}"
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(ncols)}{total_row-1}"
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 35
    ws.column_dimensions["D"].width = 22
    for col in range(5, ncols + 1):
        ws.column_dimensions[get_column_letter(col)].width = 14


def make_region_summary_sheet(ws, data,
                               sheet_label="Region Summary",
                               period_label=None):
    dark_green  = "0B6A57"
    period_fill = "E8F5F1"
    thin        = Side(style="thin", color="999999")
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)
    headers     = ["Region", "Target", "Achieved", "Gap", "Achievement %"]

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title           = ws.cell(1, 1)
    title.value     = f"Vinod Cookware — {sheet_label}"
    title.font      = Font(bold=True, color="FFFFFF", size=12)
    title.fill      = PatternFill("solid", fgColor=dark_green)
    title.alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    period_cell           = ws.cell(2, 1)
    period_cell.value     = f"Period: {period_label}" if period_label else "Period: All Data"
    period_cell.font      = Font(bold=True, color="0B3D5C", size=10)
    period_cell.fill      = PatternFill("solid", fgColor=period_fill)
    period_cell.alignment = Alignment(horizontal="center")

    header_row = 3
    for col, h in enumerate(headers, 1):
        cell           = ws.cell(header_row, col)
        cell.value     = h
        cell.font      = Font(bold=True, color="FFFFFF")
        cell.fill      = PatternFill("solid", fgColor=dark_green)
        cell.border    = border
        cell.alignment = Alignment(horizontal="center")

    row_no = header_row + 1
    for row in get_region_summary_data(data):
        ws.cell(row_no, 1).value = row["region"]
        ws.cell(row_no, 2).value = row["target"]
        ws.cell(row_no, 3).value = row["achieved"]
        ws.cell(row_no, 4).value = row["gap"]
        ws.cell(row_no, 5).value = row["achievement_percent"] / 100
        for col in range(1, 6):
            c = ws.cell(row_no, col)
            c.border = border
            if col in [2, 3, 4]:
                c.number_format = '#,##0.00'
            if col == 5:
                c.number_format = "0.00%"
        row_no += 1

    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].width = 18


def add_region_chart(ws, header_row=1):
    if ws.max_row < header_row + 1:
        return

    chart         = BarChart()
    chart.title   = "Region — Target vs Achieved"
    chart.y_axis.title = "Amount"
    chart.x_axis.title = "Region"

    data_ref = Reference(ws, min_col=2, max_col=3,
                         min_row=header_row, max_row=ws.max_row)
    cats_ref = Reference(ws, min_col=1,
                         min_row=header_row + 1, max_row=ws.max_row)

    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.height = 10
    chart.width  = 20

    anchor_row = header_row - 1 if header_row > 1 else 2
    ws.add_chart(chart, f"G{anchor_row}")


@frappe.whitelist()
def get_mis_dashboard_data(from_date=None, to_date=None, customer_group=None):
    filters = frappe._dict({
        "from_date":      from_date,
        "to_date":        to_date,
        "customer_group": customer_group or "Debtors Distributors"
    })

    categories = get_categories(filters)
    data       = get_data(filters, categories)

    total_target   = sum(flt(d.get("total_target"))   for d in data)
    total_achieved = sum(flt(d.get("total_achieved")) for d in data)
    total_gap      = total_target - total_achieved
    total_achievement = (
        total_achieved / total_target * 100 if total_target else 0
    )

    category_summary = []
    for cat in categories:
        safe     = safe_field(cat)
        target   = sum(flt(d.get(f"{safe}_target"))   for d in data)
        achieved = sum(flt(d.get(f"{safe}_achieved")) for d in data)
        gap      = target - achieved
        category_summary.append({
            "category":    cat,
            "target":      target,
            "achieved":    achieved,
            "gap":         gap,
            "achievement": achieved / target * 100 if target else 0
        })

    # >>> CHANGED: skip display-only categories that are already real columns now
    existing = {normalize(c) for c in categories}
    for cat in DISPLAY_ONLY_CATEGORIES:
        if normalize(cat) in existing:
            continue
        achieved = get_display_only_category_totals(filters, cat)
        category_summary.append({
            "category":    cat,
            "target":      0,
            "achieved":    achieved,
            "achievement": 0
        })

    AREA_FIELD_MAP = {
        "ROM":       (["parent_sales_person"], ["Sandeep Kumar"]),
        "Mumbai AH": (["parent_sales_person"], ["Muslim Abdulla Hakim (Aslam)"]),
        "Gujarat":   (["tso_name", "parent_sales_person"], ["MAYUR TALATI"]),
        "MPCG":      (["parent_sales_person", "tso_name"], ["Jaydeo Deshmukh"]),
    }

    AREA_MAP = {
        "North":     lambda r: r.get("custom_region") == "North",
        "South":     lambda r: r.get("custom_region") == "South",
        "East":      lambda r: r.get("custom_region") == "East",
        "ROM":       lambda r: row_matches_section(r, *AREA_FIELD_MAP["ROM"]),
        "Mumbai AH": lambda r: row_matches_section(r, *AREA_FIELD_MAP["Mumbai AH"]),
        "Gujarat":   lambda r: row_matches_section(r, *AREA_FIELD_MAP["Gujarat"]),
        "MPCG":      lambda r: row_matches_section(r, *AREA_FIELD_MAP["MPCG"]),
    }

    area_summary = []
    for area, condition in AREA_MAP.items():
        rows     = [x for x in data if condition(x)]
        target   = sum(flt(r.get("total_target"))   for r in rows)
        achieved = sum(flt(r.get("total_achieved")) for r in rows)
        gap      = target - achieved
        area_summary.append({
            "area":        area,
            "target":      target,
            "achieved":    achieved,
            "gap":         gap,
            "achievement": achieved / target * 100 if target else 0
        })

    # real category totals for each region
    region_category = {}
    for area, condition in AREA_MAP.items():
        area_rows = [x for x in data if condition(x)]
        region_category[area] = []
        for cat in categories:
            safe = safe_field(cat)
            t = sum(flt(r.get(f"{safe}_target"))   for r in area_rows)
            a = sum(flt(r.get(f"{safe}_achieved")) for r in area_rows)
            region_category[area].append({
                "category":    cat,
                "target":      t,
                "achieved":    a,
                "gap":         t - a,
                "achievement": a / t * 100 if t else 0
            })

    return {
        "kpi": {
            "target":      total_target,
            "achieved":    total_achieved,
            "gap":         total_gap,
            "achievement": total_achievement
        },
        "category_summary": category_summary,
        "area_summary":     area_summary,
        "region_category":  region_category
    }