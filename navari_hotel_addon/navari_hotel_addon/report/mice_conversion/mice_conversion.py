# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_conditions(filters):
    conditions = ["q.docstatus = 1", "q.quotation_template IS NOT NULL"]

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("q.transaction_date BETWEEN %(from_date)s AND %(to_date)s")
    elif filters.get("from_date"):
        conditions.append("q.transaction_date >= %(from_date)s")
    elif filters.get("to_date"):
        conditions.append("q.transaction_date <= %(to_date)s")

    if filters.get("company"):
        conditions.append("q.company = %(company)s")

    return " AND ".join(conditions)


def get_data(filters):
    conditions = get_conditions(filters)

    quotations = frappe.db.sql(f"""
        SELECT
            q.name,
            q.quotation_template,
            q.base_grand_total AS total,
            q.status
        FROM `tabQuotation` q
        WHERE {conditions}
    """, filters, as_dict=True)

    if not quotations:
        return []

    summary = {}
    for q in quotations:
        template = q.quotation_template

        if template not in summary:
            summary[template] = {
                "quotation_template": template,
                "total_quotations": 0,
                "fully_converted": 0,
                "partially_converted": 0,
                "total_value": 0.0,
                "converted_value": 0.0
            }

        s = summary[template]
        s["total_quotations"] += 1
        s["total_value"] += q.total or 0

        # Conversion classification
        if q.status == "Ordered":
            s["fully_converted"] += 1
            s["converted_value"] += q.total or 0

        elif q.status == "Partially Ordered":
            s["partially_converted"] += 1
            s["converted_value"] += q.total or 0

    # Compute conversion rates
    for s in summary.values():
        converted_total = s["fully_converted"] + s["partially_converted"]
        s["conversion_rate"] = (
            (converted_total / s["total_quotations"]) * 100
            if s["total_quotations"] else 0
        )

    return list(summary.values())

def get_columns():
    return [
        {
            "label": "Quotation Template", 
            "fieldname": "quotation_template", 
            "fieldtype": "Link",
            "options": "Terms and Conditions",
            "width": 250
        },
        {
            "label": "Total Quotations", 
            "fieldname": "total_quotations", 
            "fieldtype": "Int", 
            "width": 140
        },
        {
            "label": "Fully Ordered", 
            "fieldname": "fully_converted", 
            "fieldtype": "Int", 
            "width": 130
        },
        {
            "label": "Partially Ordered", 
            "fieldname": "partially_converted", 
            "fieldtype": "Int", 
            "width": 150
        },
        {
            "label": "Conversion Rate (%)", 
            "fieldname": "conversion_rate", 
            "fieldtype": "Percent", 
            "width": 160
        },
        {
            "label": "Total Quotation Value", 
            "fieldname": "total_value", 
            "fieldtype": "Currency", 
            "width": 150,
            "hidden": 1,
        },
        {
            "label": "Converted Value", 
            "fieldname": "converted_value", 
            "fieldtype": "Currency", 
            "width": 150,
            "hidden": 1,
        },
    ]
