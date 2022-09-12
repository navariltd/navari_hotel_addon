frappe.provide("erpnext.public");
frappe.provide("erpnext.controllers");

erpnext.taxes_and_totals.prototype.calculate_item_values = function() {
    let me = this;
    if (!this.discount_amount_applied) {
        $.each(this.frm.doc["items"] || [], function(i, item) {
            frappe.model.round_floats_in(item);
            item.net_rate = item.rate;

            if ((!item.qty) && me.frm.doc.is_return) {
                item.amount = flt(item.rate * -1, precision("amount", item));
            } else if ((!item.qty) && me.frm.doc.is_debit_note) {
                item.amount = flt(item.rate, precision("amount", item));
            } else {
                item.amount = flt(item.rate * item.qty * item.days, precision("amount", item));
            }

            item.net_amount = item.amount;
            item.item_tax_amount = 0.0;
            item.total_weight = flt(item.weight_per_unit * item.stock_qty);

            me.set_in_company_currency(item, ["price_list_rate", "rate", "amount", "net_rate", "net_amount"]);
        });
    }
}