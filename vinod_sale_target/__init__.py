# __version__ = "0.0.1"


# import frappe
# from frappe.utils import flt

# # 1. Target the core ERPNext calculations controller class
# from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

# # 2. Keep a backup copy of the standard ERPNext calculation loop
# original_calculate_item_values = calculate_taxes_and_totals.calculate_item_values

# def custom_calculate_item_values(self):
#     # Run the original standard calculations first (calculates standard fields/taxes)
#     original_calculate_item_values(self)
    
#     # Check if our custom "Weight Based Amount" checkbox is checked on the invoice
#     if self.doc.get("custom_use_weight_based_amount"):
#         for item in self.doc.get("items"):
#             weight = flt(item.get("custom_weight"))
#             rate = flt(item.rate)
            
#             # If weight and rate exist, forcefully replace the standard amount with our formula
#             if weight > 0 and rate > 0:
#                 custom_amount = flt(weight * rate, item.precision("amount"))
#                 item.amount = custom_amount
#                 item.net_amount = custom_amount
                
#                 # Update currency conversion fields securely
#                 conv = flt(self.doc.conversion_rate or 1)
#                 item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
#                 item.base_net_amount = item.base_amount

# # 3. Swap the original system method with our custom wrapper method
# calculate_taxes_and_totals.calculate_item_values = custom_calculate_item_values


import frappe
from frappe.utils import flt

# Target the core taxes calculator backend module
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

original_calculate_item_values = calculate_taxes_and_totals.calculate_item_values

def custom_calculate_item_values(self):
    # 1. Run the standard ERPNext calculation loop first
    original_calculate_item_values(self)
    
    # 2. If our weight calculation feature is active, bypass the standard amounts entirely
    if self.doc.get("custom_use_weight_based_amount"):
        for item in self.doc.get("items"):
            weight = flt(item.get("custom_weight"))
            rate = flt(item.rate)
            
            # Completely ignore item.qty here! We only care about weight * rate
            if weight > 0 and rate > 0:
                custom_amount = flt(weight * rate, item.precision("amount"))
                
                # Assign to core database fields
                item.amount = custom_amount
                item.net_amount = custom_amount
                
                # Synchronize base currency modifications
                conv = flt(self.doc.conversion_rate or 1)
                item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
                item.base_net_amount = item.base_amount

# Swap standard function with our strict quantity-isolated calculator
calculate_taxes_and_totals.calculate_item_values = custom_calculate_item_values