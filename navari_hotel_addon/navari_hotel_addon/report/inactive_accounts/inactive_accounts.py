# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

# Server-side allow-list mirroring the Select options in inactive_accounts.js.
# The single-doctype values are used as SQL table names, so they must never be free text.
SINGLE_DOCTYPES = ("Quotation", "Sales Order", "Sales Invoice")
ALLOWED_DOCTYPES = ("Last Activity (All)",) + SINGLE_DOCTYPES


def validate_doctype(doctype, allowed=ALLOWED_DOCTYPES):
    if doctype not in allowed:
        # Do not echo the rejected value: msgprint renders HTML.
        frappe.throw(_("Invalid value for filter doctype"), frappe.ValidationError)


def execute(filters=None):
    filters = filters or {}

    doctype = filters.get("doctype")
    if not doctype:
        frappe.throw(_("Please select a Doctype"))
    validate_doctype(doctype)

    for fieldname in ("last_order_from", "last_order_to"):
        if filters.get(fieldname):
            filters[fieldname] = getdate(filters[fieldname])

    columns = get_columns()
    # Default behavior: run union query if "Last Activity (All)" is selected
    if doctype == "Last Activity (All)":
        rows = get_last_activity_all(filters)
    else:
        # One query: the last order amount is computed in SQL (see get_sales_details),
        # instead of one extra query per customer row.
        # r indices: 0=name,1=customer_name,2=territory,3=group,
        #            4=num_orders,5=total_value,6=considered,7=last_order_amount,
        #            8=last_order_date,9=days_since_last_order
        rows = get_sales_details(doctype, filters)
        for r in rows:
            r.append(doctype)  # Add source doctype column
    return columns, rows


def get_sales_details(doctype, filters):
    """Builds and runs the main aggregation query, applying HAVING clauses
    for Last Week/Month/Year or a custom from-to date range."""
    validate_doctype(doctype, SINGLE_DOCTYPES)
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

    # WHERE conditions (customer and docstatus)
    where_clauses = ["so.docstatus = 1"]
    args = {}
    if filters.get("customer"):
        where_clauses.append("cust.name = %(customer)s")
        args["customer"] = filters["customer"]

    where_sql = " AND ".join(where_clauses)

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
            IFNULL((
                SELECT last_so.base_net_total
                FROM `tab{doctype}` last_so
                WHERE last_so.`{customer_field}` = cust.name
                  AND last_so.docstatus = 1
                ORDER BY last_so.`{date_field}` DESC
                LIMIT 1
            ), 0) AS last_order_amount,
            MAX(so.`{date_field}`)     AS last_order_date,
            DATEDIFF(CURDATE(), MAX(so.`{date_field}`)) AS days_since_last_order
        FROM `tabCustomer` cust
        JOIN `tab{doctype}` so
          ON cust.name = so.`{customer_field}`
        WHERE {where_sql}
        GROUP BY cust.name
    """

    clauses = []

    period = filters.get("last_order_period")
    if period == "Last Week":
        # previous Mon–Sun
        clauses.append(
            """
            last_order_date BETWEEN
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+7) DAY)
            AND
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+1) DAY)
        """.strip()
        )

    elif period == "Last Month":
        # first and last day of last calendar month
        clauses.append(
            """
            last_order_date BETWEEN
              DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE())-1 DAY), INTERVAL 1 MONTH)
            AND
              LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """.strip()
        )

    elif period == "Last Year":
        # any day in the previous calendar year
        clauses.append("YEAR(last_order_date) = YEAR(CURDATE()) - 1")

    # Custom date range overrides the period
    if filters.get("last_order_from") and filters.get("last_order_to"):
        clauses.append("last_order_date BETWEEN %(from)s AND %(to)s")
        args.update(
            {
                "from": filters["last_order_from"],
                "to": filters["last_order_to"],
            }
        )

    having = clauses and ("HAVING " + " AND ".join(clauses)) or ""
    query = f"""{base}
				{having}
				ORDER BY last_order_date DESC, cust.name
			"""

    return frappe.db.sql(query, args, as_list=1)


def get_last_activity_all(filters):
    """Get most recent activity across Quotation, Sales Order, and Sales Invoice for each customer,
    applying period/date range filters."""

    mapping = [
        ("Quotation", "party_name", "transaction_date"),
        ("Sales Order", "customer", "transaction_date"),
        ("Sales Invoice", "customer", "posting_date"),
    ]

    period_filter_sql, date_args = build_period_filters(filters)

    # Customer filter
    customer_condition = ""
    if filters.get("customer"):
        customer_condition = "AND cust.name = %(customer)s"
        date_args["customer"] = filters["customer"]

    queries = []
    for doctype, customer_field, date_field in mapping:
        queries.append(f"""
            SELECT
                cust.name AS customer,
                cust.customer_name,
                cust.territory,
                cust.customer_group,
                1 AS num_of_order,
                so.base_net_total AS total_order_value,
                so.base_net_total AS total_order_considered,
                so.base_net_total AS last_order_amount,
                so.`{date_field}` AS last_order_date,
                DATEDIFF(CURDATE(), so.`{date_field}`) AS days_since_last_order,
                '{doctype}' AS source_doctype
            FROM `tabCustomer` cust
            JOIN `tab{doctype}` so
              ON cust.name = so.`{customer_field}`
              AND so.docstatus = 1
            WHERE 1=1
              {customer_condition}
            {period_filter_sql.replace("last_order_date", f"so.`{date_field}`")}
        """)

    union_query = " UNION ALL ".join(queries)

    # Wrap to get only the latest per customer
    final_query = f"""
        SELECT t.* 
        FROM (
            {union_query}
        ) AS t
        INNER JOIN (
            SELECT customer, MAX(last_order_date) AS max_date
            FROM ({union_query}) AS sub
            GROUP BY customer
        ) AS latest
        ON t.customer = latest.customer
        AND t.last_order_date = latest.max_date
        ORDER BY t.last_order_date DESC
    """

    return frappe.db.sql(final_query, date_args, as_list=1)


def build_period_filters(filters):
    """Return SQL WHERE clause and args for period or custom date range."""
    clauses = []
    args = {}

    period = filters.get("last_order_period")
    if period == "Last Week":
        clauses.append("""
            last_order_date BETWEEN
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+7) DAY)
            AND
              DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE())+1) DAY)
        """)
    elif period == "Last Month":
        clauses.append("""
            last_order_date BETWEEN
              DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE())-1 DAY), INTERVAL 1 MONTH)
            AND
              LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """)
    elif period == "Last Year":
        clauses.append("YEAR(last_order_date) = YEAR(CURDATE()) - 1")

    if filters.get("last_order_from") and filters.get("last_order_to"):
        clauses.append("last_order_date BETWEEN %(from)s AND %(to)s")
        args.update(
            {
                "from": filters["last_order_from"],
                "to": filters["last_order_to"],
            }
        )

    where_sql = f"AND {' AND '.join(clauses)}" if clauses else ""

    return where_sql, args


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
        _("Type") + "::140",
    ]
