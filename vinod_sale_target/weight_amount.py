# import frappe
# from frappe.utils import flt

# def apply_weight_based_amount(doc, method=None):
#     # If checkbox is not checked, act completely standard
#     if not doc.get("custom_use_weight_based_amount"):
#         return

#     # Pass 1: Set our weights
#     force_weight_math(doc)

#     # Compute raw parent aggregates
#     net_total = sum(flt(item.net_amount) for item in doc.items)
#     base_net_total = sum(flt(item.base_net_amount) for item in doc.items)

#     doc.net_total = flt(net_total, doc.precision("net_total"))
#     doc.total = doc.net_total
#     doc.base_net_total = flt(base_net_total, doc.precision("base_net_total"))
#     doc.base_total = doc.base_net_total

#     # Execute core taxes layout mechanics
#     doc.calculate_taxes_and_totals()

#     # Pass 2: Hard-lock after the core calculator tries to overwrite it
#     force_weight_math(doc)

#     # Clean total aggregation block
#     tax_total = sum(flt(t.tax_amount_after_discount_amount) for t in doc.get("taxes") or [])
#     doc.grand_total = flt(doc.net_total + tax_total, doc.precision("grand_total"))
#     doc.base_grand_total = flt(doc.base_net_total + (tax_total * flt(doc.conversion_rate or 1)), doc.precision("base_grand_total"))
    
#     doc.rounded_total = flt(round(doc.grand_total), doc.precision("rounded_total"))
#     doc.base_rounded_total = flt(round(doc.base_grand_total), doc.precision("base_rounded_total"))
#     doc.outstanding_amount = doc.rounded_total if doc.rounded_total > 0 else doc.grand_total

# def force_weight_math(doc):
#     """Helper method that strictly overrides row amounts to Weight * Rate"""
#     for item in doc.get("items"):
#         weight = flt(item.get("custom_weight"))
#         rate = flt(item.rate)

#         if weight > 0 and rate > 0:
#             custom_amount = flt(weight * rate, item.precision("amount"))
            
#             item.amount = custom_amount
#             item.net_amount = custom_amount
            
#             conv = flt(doc.conversion_rate or 1)
#             item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
#             item.base_net_amount = item.base_amount
#             item.net_rate = rate
#             item.base_net_rate = flt(rate * conv, item.precision("base_net_rate"))



import frappe
from frappe.utils import flt

SUPPORTED_DOCTYPES = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]


def apply_weight_based_amount(doc, method=None):
    if doc.doctype not in SUPPORTED_DOCTYPES:
        return

    if not doc.get("custom_use_weight_based_amount"):
        return

    force_weight_math(doc)

    net_total = sum(flt(item.net_amount) for item in doc.items)
    base_net_total = sum(flt(item.base_net_amount) for item in doc.items)

    doc.net_total = flt(net_total, doc.precision("net_total"))
    doc.total = doc.net_total
    doc.base_net_total = flt(base_net_total, doc.precision("base_net_total"))
    doc.base_total = doc.base_net_total

    doc.calculate_taxes_and_totals()

    force_weight_math(doc)

    tax_total = sum(flt(t.tax_amount_after_discount_amount) for t in doc.get("taxes") or [])
    doc.grand_total = flt(doc.net_total + tax_total, doc.precision("grand_total"))
    doc.base_grand_total = flt(
        doc.base_net_total + (tax_total * flt(doc.conversion_rate or 1)),
        doc.precision("base_grand_total")
    )

    doc.rounded_total = flt(round(doc.grand_total), doc.precision("rounded_total"))
    doc.base_rounded_total = flt(round(doc.base_grand_total), doc.precision("base_rounded_total"))
    doc.outstanding_amount = doc.rounded_total if doc.rounded_total > 0 else doc.grand_total


def force_weight_math(doc):
    """Strictly overrides row amounts to Weight * Rate"""
    for item in doc.get("items"):
        weight = flt(item.get("custom_weight"))
        rate = flt(item.rate)

        if weight > 0 and rate > 0:
            custom_amount = flt(weight * rate, item.precision("amount"))

            item.amount = custom_amount
            item.net_amount = custom_amount

            conv = flt(doc.conversion_rate or 1)
            item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
            item.base_net_amount = item.base_amount
            item.net_rate = rate
            item.base_net_rate = flt(rate * conv, item.precision("base_net_rate"))