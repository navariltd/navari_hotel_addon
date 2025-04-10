frappe.ui.form.on("Sales Order", {
    
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && !["Completed", "Cancelled"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Set as Lost"), function() {
                frm.trigger("set_as_lost_dialog");
            }, __("Status"));
        }
    },

    set_as_lost_dialog: function(frm) {
        // Create a dialog to confirm and optionally capture a reason
        let dialog = new frappe.ui.Dialog({
            title: __("Set Sales Order as Lost"),
            fields: [
                {
                    fieldname: "lost_reasons",
                    fieldtype: "Table MultiSelect",
                    options: "Sales Order Lost Reason Detail",
                    label: __("Lost Reason"),
                    default: frm.doc.lost_reasons || [],
                },
                {
                    fieldname: "competitor",
                    fieldtype: "Link",
                    options: "Competitor",
                    label: __("Competitor"),
                    default: frm.doc.competitor || "",
                },
                {
                    fieldname: "detailed_reason",
                    fieldtype: "Small Text",
                    label: __("Detailed Reason"),
                    default: frm.doc.detailed_reason || "",
                }
            ],
            primary_action_label: __("Confirm"),
            primary_action: function(values) {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "Sales Order",
                        name: frm.doc.name,
                        fieldname: {
                            "lost_reasons": values.lost_reasons,
                            "competitor": values.competitor,
                            "detailed_reason": values.detailed_reason
                        }
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frm.save("Cancel");
                            frm.reload_doc();
                        }
                    }
                });
                dialog.hide();
            }
        });
        dialog.show();
    },
})
