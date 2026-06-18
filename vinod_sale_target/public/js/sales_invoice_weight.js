// frappe.ui.form.on("Sales Invoice", {
//     refresh(frm) {
//         toggle_weight_hint(frm);
//     },
//     custom_use_weight_based_amount(frm) {
//         toggle_weight_hint(frm);
//         run_weight_calculations(frm);
//     }
// });

// frappe.ui.form.on("Sales Invoice Item", {
//     custom_weight(frm, cdt, cdn) {
//         calculate_row_weight_amount(frm, cdt, cdn);
//     },
    
//     rate(frm, cdt, cdn) {
//         calculate_row_weight_amount(frm, cdt, cdn);
//     },
    
//     qty(frm, cdt, cdn) {
//         calculate_row_weight_amount(frm, cdt, cdn);
//     },

//     items_remove(frm) {
//         run_weight_calculations(frm);
//     }
// });

// // Calculate for a single specific row instantly as the user types
// function calculate_row_weight_amount(frm, cdt, cdn) {
//     if (!frm.doc.custom_use_weight_based_amount) return;

//     let item = frappe.get_doc(cdt, cdn);
//     let weight = flt(item.custom_weight);
//     let rate = flt(item.rate);

//     if (weight > 0 && rate > 0) {
//         let target_amount = flt(weight * rate, precision("amount", item));
        
//         // Using frappe.model.set_value updates the UI cell instantly before saving!
//         frappe.model.set_value(cdt, cdn, "amount", target_amount);
//         frappe.model.set_value(cdt, cdn, "net_amount", target_amount);
        
//         let conv = flt(frm.doc.conversion_rate || 1);
//         frappe.model.set_value(cdt, cdn, "base_amount", flt(target_amount * conv, precision("base_amount", item)));
//         frappe.model.set_value(cdt, cdn, "base_net_amount", flt(target_amount * conv, precision("base_net_amount", item)));
//     }
    
//     // Trigger total summary recalculations
//     run_weight_calculations(frm);
// }

// // Global form calculation cleanup
// function run_weight_calculations(frm) {
//     if (!frm.doc.custom_use_weight_based_amount) return;

//     let net_total = 0;
//     (frm.doc.items || []).forEach(row => {
//         net_total += flt(row.net_amount);
//     });

//     // Explicitly update parent form header totals
//     frm.doc.net_total = net_total;
//     frm.doc.total = net_total;
    
//     frm.refresh_field("net_total");
//     frm.refresh_field("total");

//     // Force core system to process taxes based on our manual total allocations
//     if (frm.script_manager && typeof frm.script_manager.trigger === "function") {
//         frm.cscript.calculate_taxes_and_totals(frm.doc);
        
//         let tax_total = 0;
//         (frm.doc.taxes || []).forEach(t => {
//             tax_total += flt(t.tax_amount_after_discount_amount);
//         });
        
//         let ultimate_total = frm.doc.net_total + tax_total;
//         frm.doc.grand_total = flt(ultimate_total, precision("grand_total"));
//         frm.doc.rounded_total = Math.round(frm.doc.grand_total);
//         frm.doc.outstanding_amount = frm.doc.rounded_total;
        
//         frm.refresh_field("grand_total");
//         frm.refresh_field("rounded_total");
//         frm.refresh_field("outstanding_amount");
//     }
// }

// function toggle_weight_hint(frm) {
//     if (frm.doc.custom_use_weight_based_amount) {
//         frm.dashboard.set_headline(
//             __("Weight Based Amount Strategy Active (Weight × Rate Override).")
//         );
//     } else {
//         frm.dashboard.clear_headline();
//     }
// }



frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        toggle_weight_hint(frm);
    },
    custom_use_weight_based_amount(frm) {
        toggle_weight_hint(frm);
        run_weight_calculations(frm);
    }
});

frappe.ui.form.on("Sales Invoice Item", {
    custom_weight(frm, cdt, cdn) {
        calculate_row_weight_amount(frm, cdt, cdn);
    },
    
    rate(frm, cdt, cdn) {
        calculate_row_weight_amount(frm, cdt, cdn);
    },
    
    // CRITICAL FIX: Intercept the quantity field change event
    qty(frm, cdt, cdn) {
        calculate_row_weight_amount(frm, cdt, cdn);
    },

    items_remove(frm) {
        run_weight_calculations(frm);
    }
});

// Calculate for a single specific row instantly as the user types
function calculate_row_weight_amount(frm, cdt, cdn) {
    if (!frm.doc.custom_use_weight_based_amount) return;

    let item = frappe.get_doc(cdt, cdn);
    let weight = flt(item.custom_weight);
    let rate = flt(item.rate);

    // No matter what the qty is (2, 10, 50), strictly enforce Weight * Rate
    if (weight > 0 && rate > 0) {
        let target_amount = flt(weight * rate, precision("amount", item));
        
        // Use frappe.model.set_value to broadcast the change across the UI layout
        frappe.model.set_value(cdt, cdn, "amount", target_amount);
        frappe.model.set_value(cdt, cdn, "net_amount", target_amount);
        
        let conv = flt(frm.doc.conversion_rate || 1);
        frappe.model.set_value(cdt, cdn, "base_amount", flt(target_amount * conv, precision("base_amount", item)));
        frappe.model.set_value(cdt, cdn, "base_net_amount", flt(target_amount * conv, precision("base_net_amount", item)));
    }
    
    // Trigger parent summary updates
    run_weight_calculations(frm);
}

// Global parent form total aggregator
function run_weight_calculations(frm) {
    if (!frm.doc.custom_use_weight_based_amount) return;

    let net_total = 0;
    (frm.doc.items || []).forEach(row => {
        net_total += flt(row.net_amount);
    });

    frm.doc.net_total = net_total;
    frm.doc.total = net_total;
    
    frm.refresh_field("net_total");
    frm.refresh_field("total");

    // Force tax calculation using our explicit net allocations
    if (frm.script_manager && typeof frm.script_manager.trigger === "function") {
        frm.cscript.calculate_taxes_and_totals(frm.doc);
        
        let tax_total = 0;
        (frm.doc.taxes || []).forEach(t => {
            tax_total += flt(t.tax_amount_after_discount_amount);
        });
        
        let ultimate_total = frm.doc.net_total + tax_total;
        frm.doc.grand_total = flt(ultimate_total, precision("grand_total"));
        frm.doc.rounded_total = Math.round(frm.doc.grand_total);
        frm.doc.outstanding_amount = frm.doc.rounded_total;
        
        frm.refresh_field("grand_total");
        frm.refresh_field("rounded_total");
        frm.refresh_field("outstanding_amount");
    }
}

function toggle_weight_hint(frm) {
    if (frm.doc.custom_use_weight_based_amount) {
        frm.dashboard.set_headline(
            __("Weight Based Amount Strategy Active (Weight × Rate Override).")
        );
    } else {
        frm.dashboard.clear_headline();
    }
}