from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


def calculate_item_values(self):
    if self.doc.get("is_consolidated") or self.discount_amount_applied:
        return

    do_not_round_fields = ["valuation_rate", "incoming_rate", "sales_incoming_rate"]
    for item in self._items:
        self.doc.round_floats_in(item, do_not_round_fields=do_not_round_fields)
        self.calculate_item_rate(item)

        item.net_rate = item.rate

        if (
            not item.qty
            and self.doc.get("is_return")
            and self.doc.get("doctype") != "Purchase Receipt"
        ):
            item.amount = flt(-1 * item.rate, item.precision("amount"))
        elif not item.qty and self.doc.get("is_debit_note"):
            item.amount = flt(item.rate, item.precision("amount"))
        else:
            item.amount = flt(
                item.rate * item.qty * item.days, item.precision("amount")
            )

        item.net_amount = item.amount

        self._set_in_company_currency(
            item,
            [
                "price_list_rate",
                "rate_with_margin",
                "rate",
                "net_rate",
                "amount",
                "net_amount",
            ],
        )

        item.item_tax_amount = 0.0


calculate_taxes_and_totals.calculate_item_values = calculate_item_values
