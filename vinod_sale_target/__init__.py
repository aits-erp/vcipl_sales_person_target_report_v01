
# import frappe
# from frappe.utils import flt

# # Target the core taxes calculator backend module
# from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

# original_calculate_item_values = calculate_taxes_and_totals.calculate_item_values

# def custom_calculate_item_values(self):
#     # 1. Run the standard ERPNext calculation loop first
#     original_calculate_item_values(self)
    
#     # 2. If our weight calculation feature is active, bypass the standard amounts entirely
#     if self.doc.get("custom_use_weight_based_amount"):
#         for item in self.doc.get("items"):
#             weight = flt(item.get("custom_weight"))
#             rate = flt(item.rate)
            
#             # Completely ignore item.qty here! We only care about weight * rate
#             if weight > 0 and rate > 0:
#                 custom_amount = flt(weight * rate, item.precision("amount"))
                
#                 # Assign to core database fields
#                 item.amount = custom_amount
#                 item.net_amount = custom_amount
                
#                 # Synchronize base currency modifications
#                 conv = flt(self.doc.conversion_rate or 1)
#                 item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
#                 item.base_net_amount = item.base_amount

# # Swap standard function with our strict quantity-isolated calculator
# calculate_taxes_and_totals.calculate_item_values = custom_calculate_item_values



# Keep standard metadata clear and readable for python packaging engines
__version__ = "0.0.1"

# Safe initialization wrapper block
try:
    import frappe
    from frappe.utils import flt
    from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

    # Keep a backup copy of the standard ERPNext calculation loop
    original_calculate_item_values = calculate_taxes_and_totals.calculate_item_values

    def custom_calculate_item_values(self):
        # 1. Run the standard ERPNext calculation loop first
        original_calculate_item_values(self)
        
        # 2. If our weight calculation feature is active, bypass standard amounts completely
        if self.doc.get("custom_use_weight_based_amount"):
            for item in self.doc.get("items"):
                weight = flt(item.get("custom_weight"))
                rate = flt(item.rate)
                
                # Completely ignore item.qty here! We only care about weight * rate
                if weight > 0 and rate > 0:
                    custom_amount = flt(weight * rate, item.precision("amount"))
                    
                    # Assign directly to core database fields
                    item.amount = custom_amount
                    item.net_amount = custom_amount
                    
                    # Synchronize base currency modifications securely
                    conv = flt(self.doc.conversion_rate or 1)
                    item.base_amount = flt(custom_amount * conv, item.precision("base_amount"))
                    item.base_net_amount = item.base_amount

    # Swap standard function with our strict quantity-isolated calculator
    calculate_taxes_and_totals.calculate_item_values = custom_calculate_item_values

except (ImportError, ModuleNotFoundError):
    # If frappe isn't fully installed yet (like during bench get-app / pip installs / docker builds)
    # pass silently so the package metadata can successfully compile
    pass