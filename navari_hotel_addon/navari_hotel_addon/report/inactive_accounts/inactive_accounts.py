# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint


def execute(filters=None):
    filters = filters or {}

    doctype = filters.get("doctype")
    if not doctype:
        frappe.throw(_("Please select a Doctype"))

    columns = get_columns()

    # 1. Fetch data (SQL includes HAVING based on period or custom dates)
    rows = get_sales_details(doctype, filters)

    # 2. For each row, insert the value of the very last order before returning
    data = []
    for r in rows:
        # r indices: 0=name,1=customer_name,2=territory,3=group,
        #            4=num_orders,5=total_value,6=considered,
        #            7=last_order_date,8=days_since_last_order
        last_amt = get_last_sales_amt(r[0], doctype)
        r.insert(7, last_amt)
        data.append(r)

    return columns, data


def get_sales_details(doctype, filters):
    """Builds and runs the main aggregation query, applying HAVING clauses
    for Last Week/Month/Year or a custom from-to date range."""
    customer_field = "party_name" if doctype == "Quotation" else "customer"
    if doctype in ("Sales Order", "Quotation"):
        date_field = "transaction_date"
    else:
        date_field = "posting_date"
        
	# Only sales order needs the IF(per_delivered) logic
    if doctype == "Sales Order":
        total_considered = """
            SUM(
                IF(so.status='Stopped',
                so.base_net_total * IFNULL(so.per_delivered, 0)/100,
                so.base_net_total)
            ) AS total_order_considered
        """
    else:
        total_considered = "SUM(so.base_net_total) AS total_order_considered"

    # Base aggregation
    base = f"""
        SELECT
            cust.name,
            cust.customer_name,
            cust.territory,
            cust.customer_group,
            COUNT(DISTINCT so.name) AS num_of_order,
            SUM(so.base_net_total)    AS total_order_value,
            {total_considered},
            MAX(so.`{date_field}`)     AS last_order_date,
            DATEDIFF(CURDATE(), MAX(so.`{date_field}`)) AS days_since_last_order
        FROM `tabCustomer` cust
        JOIN `tab{doctype}` so
          ON cust.name = so.`{customer_field}`
         AND so.docstatus = 1
        GROUP BY cust.name
    """

    clauses = []
    args    = {}

    period = filters.get("last_order_period")
    if period == "Last Week":
        # previous Mon–Sun
        clauses.append("""
            last_order_date BETWEEN
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+7) DAY)
            AND
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+1) DAY)
        """.strip())

    elif period == "Last Month":
        # first and last day of last calendar month
        clauses.append("""
            last_order_date BETWEEN
              DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE())-1 DAY), INTERVAL 1 MONTH)
            AND
              LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """.strip())

    elif period == "Last Year":
        # any day in the previous calendar year
        clauses.append("YEAR(last_order_date) = YEAR(CURDATE()) - 1")

    # Custom date range overrides the period
    if filters.get("last_order_from") and filters.get("last_order_to"):
        clauses.append("last_order_date BETWEEN %(from)s AND %(to)s")
        args.update({
            "from": filters["last_order_from"],
            "to":   filters["last_order_to"],
        })

    having = clauses and ("HAVING " + " AND ".join(clauses)) or ""
    query  = f"""{base}
				{having}
				ORDER BY last_order_date DESC
			"""

    return frappe.db.sql(query, args, as_list=1)


def get_last_sales_amt(customer, doctype):
    """Fetch the base_net_total of the single most-recent record."""
    customer_field = "party_name" if doctype == "Quotation" else "customer"
    date_field     = doctype in ("Sales Order", "Quotation") and "transaction_date" or "posting_date"

    res = frappe.db.sql(
        f"""SELECT base_net_total
            FROM `tab{doctype}`
            WHERE `{customer_field}` = %s
              AND docstatus = 1
            ORDER BY `{date_field}` DESC
            LIMIT 1""",
        customer,
    )
    return (res and res[0][0]) or 0


def get_columns():
	return [
		_("Customer") + ":Link/Customer:120",
		_("Customer Name") + ":Data:120",
		_("Territory") + "::120",
		_("Customer Group") + "::120",
		_("Number of Order") + "::120",
		_("Total Order Value") + ":Currency:120",
		_("Total Order Considered") + ":Currency:160",
		_("Last Order Amount") + ":Currency:160",
		_("Last Order Date") + ":Date:160",
		_("Days Since Last Order") + "::160",
	]
