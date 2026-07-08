# import frappe
# from frappe.utils import flt

# SUPPORTED_DOCTYPES = [
#     "Purchase Order",
#     "Purchase Invoice",
#     "Purchase Receipt",
#     "Material Request",
#     "Stock Entry",
#     "Delivery Note",
#     "Sales Order",
#     "Quotation",
#     "Sales Invoice"
# ]


# def apply_weight_based_amount(doc, method=None):
#     if doc.doctype not in SUPPORTED_DOCTYPES:
#         return

#     if not doc.get("custom_use_weight_based_amount"):
#         return

#     # Pass 1: set weight amounts
#     force_weight_math(doc)

#     net_total = sum(flt(_get_amount(item)) for item in doc.items)
#     base_net_total = sum(flt(_get_base_amount(item)) for item in doc.items)

#     if doc.meta.has_field("net_total"):
#         doc.net_total = flt(net_total, doc.precision("net_total"))
#     if doc.meta.has_field("total"):
#         doc.total = net_total
#     if doc.meta.has_field("base_net_total"):
#         doc.base_net_total = flt(base_net_total, doc.precision("base_net_total"))
#     if doc.meta.has_field("base_total"):
#         doc.base_total = base_net_total

#     # Let ERPNext recalculate taxes (this resets item amounts — we fix below)
#     if hasattr(doc, "calculate_taxes_and_totals"):
#         doc.calculate_taxes_and_totals()

#     # Pass 2: force amounts again after ERPNext resets them
#     force_weight_math(doc)

#     # Rebuild totals manually after force
#     net_total = sum(flt(_get_amount(item)) for item in doc.items)
#     base_net_total = sum(flt(_get_base_amount(item)) for item in doc.items)

#     if doc.meta.has_field("net_total"):
#         doc.net_total = flt(net_total, doc.precision("net_total"))
#     if doc.meta.has_field("total"):
#         doc.total = doc.net_total
#     if doc.meta.has_field("base_net_total"):
#         doc.base_net_total = flt(base_net_total, doc.precision("base_net_total"))
#     if doc.meta.has_field("base_total"):
#         doc.base_total = doc.base_net_total

#     if doc.meta.has_field("grand_total"):
#         tax_total = sum(flt(t.tax_amount_after_discount_amount) for t in doc.get("taxes") or [])

#         doc.grand_total = flt(net_total + tax_total, doc.precision("grand_total"))

#         if doc.meta.has_field("base_grand_total"):
#             doc.base_grand_total = flt(
#                 base_net_total + (tax_total * flt(doc.get("conversion_rate") or 1)),
#                 doc.precision("base_grand_total")
#             )

#         if doc.meta.has_field("rounded_total"):
#             doc.rounded_total = flt(round(doc.grand_total), doc.precision("rounded_total"))

#         if doc.meta.has_field("base_rounded_total"):
#             doc.base_rounded_total = flt(
#                 round(doc.get("base_grand_total") or doc.grand_total),
#                 doc.precision("base_rounded_total")
#             )

#         if doc.meta.has_field("outstanding_amount"):
#             doc.outstanding_amount = doc.get("rounded_total") or doc.grand_total


# def force_weight_math(doc):
#     for item in doc.get("items"):
#         weight = flt(item.get("custom_weight"))
#         rate = flt(item.get("rate") or item.get("basic_rate") or 0)

#         if weight <= 0 or rate <= 0:
#             continue

#         prec = item.precision("amount") if item.meta.has_field("amount") else 2
#         custom_amount = flt(weight * rate, prec)

#         if item.meta.has_field("amount"):
#             item.amount = custom_amount
#         if item.meta.has_field("net_amount"):
#             item.net_amount = custom_amount

#         conv = flt(doc.get("conversion_rate") or 1)
#         if item.meta.has_field("base_amount"):
#             item.base_amount = flt(custom_amount * conv)
#         if item.meta.has_field("base_net_amount"):
#             item.base_net_amount = flt(custom_amount * conv)
#         if item.meta.has_field("net_rate"):
#             item.net_rate = rate
#         if item.meta.has_field("base_net_rate"):
#             item.base_net_rate = flt(rate * conv)
#         if item.meta.has_field("basic_rate"):
#             item.basic_rate = rate
#         if item.meta.has_field("basic_amount"):
#             item.basic_amount = custom_amount


# def _get_amount(item):
#     return item.get("net_amount") or item.get("amount") or item.get("basic_amount") or 0


# def _get_base_amount(item):
#     return item.get("base_net_amount") or item.get("base_amount") or 0



import frappe
from frappe.utils import flt

SUPPORTED_DOCTYPES = [
    "Purchase Order",
    "Purchase Invoice",
    "Purchase Receipt",
    "Material Request",
    "Stock Entry",
    "Delivery Note",
    "Sales Order",
    "Quotation",
    "Sales Invoice"
]


def apply_weight_based_amount(doc, method=None):
    if doc.doctype not in SUPPORTED_DOCTYPES:
        return

    if not doc.get("custom_use_weight_based_amount"):
        return

    # 1. First set item amount as Weight × Rate
    force_weight_math(doc)

    # 2. Set parent totals from item table
    set_parent_totals(doc)

    # 3. Recalculate ERPNext taxes/totals
    if hasattr(doc, "calculate_taxes_and_totals"):
        doc.calculate_taxes_and_totals()

    # 4. ERPNext may overwrite item amounts, so apply again
    force_weight_math(doc)

    # 5. Set totals again
    set_parent_totals(doc)

    # 6. Correct taxes manually for Add/Deduct
    calculate_tax_totals_correctly(doc)

    # 7. Final rounded total
    set_rounded_total(doc)


def force_weight_math(doc):
    for item in doc.get("items", []):
        weight = flt(item.get("custom_weight"))
        rate = flt(item.get("rate") or item.get("basic_rate") or 0)

        if weight <= 0 or rate <= 0:
            continue

        amount_precision = item.precision("amount") if item.meta.has_field("amount") else 2
        custom_amount = flt(weight * rate, amount_precision)

        conv = flt(doc.get("conversion_rate") or 1)

        if item.meta.has_field("qty"):
            item.qty = weight

        if item.meta.has_field("amount"):
            item.amount = custom_amount

        if item.meta.has_field("net_amount"):
            item.net_amount = custom_amount

        if item.meta.has_field("base_amount"):
            item.base_amount = flt(custom_amount * conv)

        if item.meta.has_field("base_net_amount"):
            item.base_net_amount = flt(custom_amount * conv)

        if item.meta.has_field("net_rate"):
            item.net_rate = rate

        if item.meta.has_field("base_net_rate"):
            item.base_net_rate = flt(rate * conv)

        if item.meta.has_field("basic_rate"):
            item.basic_rate = rate

        if item.meta.has_field("basic_amount"):
            item.basic_amount = custom_amount


def set_parent_totals(doc):
    net_total = sum(flt(_get_amount(item)) for item in doc.get("items", []))
    base_net_total = sum(flt(_get_base_amount(item)) for item in doc.get("items", []))

    if doc.meta.has_field("net_total"):
        doc.net_total = flt(net_total, doc.precision("net_total"))

    if doc.meta.has_field("total"):
        doc.total = doc.net_total

    if doc.meta.has_field("base_net_total"):
        doc.base_net_total = flt(base_net_total, doc.precision("base_net_total"))

    if doc.meta.has_field("base_total"):
        doc.base_total = doc.base_net_total


def calculate_tax_totals_correctly(doc):
    if not doc.meta.has_field("taxes") or not doc.get("taxes"):
        final_total = flt(doc.get("net_total"))
        final_base_total = flt(doc.get("base_net_total") or final_total)

        if doc.meta.has_field("grand_total"):
            doc.grand_total = final_total

        if doc.meta.has_field("base_grand_total"):
            doc.base_grand_total = final_base_total

        return

    running_total = flt(doc.get("net_total"))
    base_running_total = flt(doc.get("base_net_total") or running_total)

    for tax in doc.get("taxes", []):
        tax_amount = flt(tax.get("tax_amount"))
        base_tax_amount = flt(tax.get("base_tax_amount") or tax_amount)

        # For Actual tax type, keep existing tax_amount
        # For rate-based tax, ERPNext already calculated tax_amount
        if tax.get("add_deduct_tax") == "Deduct":
            running_total -= tax_amount
            base_running_total -= base_tax_amount
        else:
            running_total += tax_amount
            base_running_total += base_tax_amount

        if tax.meta.has_field("total"):
            tax.total = flt(running_total)

        if tax.meta.has_field("base_total"):
            tax.base_total = flt(base_running_total)

    if doc.meta.has_field("grand_total"):
        doc.grand_total = flt(running_total, doc.precision("grand_total"))

    if doc.meta.has_field("base_grand_total"):
        doc.base_grand_total = flt(base_running_total, doc.precision("base_grand_total"))


def set_rounded_total(doc):
    grand_total = flt(doc.get("grand_total"))

    if doc.meta.has_field("rounded_total"):
        doc.rounded_total = round(grand_total)

    if doc.meta.has_field("base_rounded_total"):
        doc.base_rounded_total = round(flt(doc.get("base_grand_total") or grand_total))

    if doc.meta.has_field("rounding_adjustment"):
        doc.rounding_adjustment = flt(doc.rounded_total - grand_total)

    if doc.meta.has_field("outstanding_amount") and doc.doctype in ["Sales Invoice", "Purchase Invoice"]:
        doc.outstanding_amount = doc.rounded_total or grand_total


def _get_amount(item):
    return item.get("net_amount") or item.get("amount") or item.get("basic_amount") or 0


def _get_base_amount(item):
    return item.get("base_net_amount") or item.get("base_amount") or 0