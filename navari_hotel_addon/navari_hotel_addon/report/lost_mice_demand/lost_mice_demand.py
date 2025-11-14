# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    where_clause = build_conditions(filters)
    
    quotations = get_quotations(where_clause, filters)
    quotation_lost_reasons = get_lost_reasons(quotations, filters)
    ageing_limits = parse_ageing_buckets(filters.get("ageing_buckets"))
    bucket_labels = get_bucket_labels(ageing_limits)
    measure_by = filters.get("measure_by", "Pax")
    
    result_data = aggregate_quotations(quotations, quotation_lost_reasons, ageing_limits, bucket_labels, measure_by)
    result_data.sort(key=lambda x: x["lost_reason"])
    columns = build_columns(bucket_labels)

    return columns, result_data


def build_conditions(filters):
    conditions = ["q.docstatus = 1", "q.status = 'Lost'"]

    if filters.get("from_date"):
        conditions.append("q.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("q.transaction_date <= %(to_date)s")

    if filters.get("sales_person"):
        sales_person_user = filters.get("sales_person")
        sales_person_email = frappe.db.get_value("User", sales_person_user, "email")
        sales_person_name = frappe.db.get_value("User", sales_person_user, "full_name")
        email_condition = f"q.account_manager_email = '{sales_person_email}'" if sales_person_email else "1=0"
        name_condition = f"q.account_manager_name = '{sales_person_name}'" if sales_person_name else "1=0"
        conditions.append(f"({email_condition} OR {name_condition})")

    if filters.get("customer"):
        conditions.append("q.party_name = %(customer)s")
    if filters.get("customer_group"):
        conditions.append("q.customer_group = %(customer_group)s")

    return " AND ".join(conditions) if conditions else "1=1"


def get_quotations(where_clause, filters):
    query = f"""
        SELECT
            q.name AS quotation,
            q.customer_name,
            q.customer_group,
            q.territory,
            q.total_qty,
            q.base_grand_total,
            (
                SELECT SUM(qi.qty * IFNULL(qi.days, 1))
                FROM `tabQuotation Item` qi
                WHERE qi.parent = q.name
            ) AS total_pax_days
        FROM `tabQuotation` q
        WHERE {where_clause}
    """
    return frappe.db.sql(query, filters, as_dict=True)


def get_lost_reasons(quotations, filters):
    if not quotations:
        return {}

    quotation_names = [q['quotation'] for q in quotations]
    query = """
        SELECT 
            parent AS quotation,
            lost_reason AS reason
        FROM `tabQuotation Lost Reason Detail`
        WHERE parent IN %(quotation_names)s
    """
    if filters.get("lost_reason"):
        query += " AND lost_reason = %(lost_reason)s"

    data = frappe.db.sql(
        query, 
        {"quotation_names": quotation_names, "lost_reason": filters.get("lost_reason")}, 
        as_dict=True
    )

    # Map lost reasons to quotations
    result = {}
    for lr in data:
        result.setdefault(lr['quotation'], []).append(lr['reason'])
    return result


def parse_ageing_buckets(bucket_string):
    limits = []
    if bucket_string:
        for x in bucket_string.split(","):
            try:
                limits.append(int(x.strip()))
            except ValueError:
                continue
    if not limits:
        limits = [20, 80]  # default
    return sorted(limits)


def aggregate_quotations(quotations, quotation_lost_reasons, ageing_limits, bucket_labels, measure_by):
    summary = {}

    for q in quotations:
        quotation_name = q['quotation']
        lost_reason_list = quotation_lost_reasons.get(quotation_name, ["Not Specified"])

        measure_value = q.get("total_pax_days") if measure_by == "Pax-Days" else q.get("total_qty") or 0
        bucket = get_ageing_bucket(measure_value, ageing_limits)

        for lost_reason in lost_reason_list:
            if lost_reason not in summary:
                summary[lost_reason] = {label: 0 for label in bucket_labels}
                summary[lost_reason].update({
                    "lost_reason": lost_reason,
                    "total_quotations": 0,
                    "total_pax": 0,
                    "total_pax_days": 0,
                    "total_value": 0
                })

            summary[lost_reason][bucket] += 1
            summary[lost_reason]["total_quotations"] += 1
            summary[lost_reason]["total_pax"] += q.get("total_qty") or 0
            summary[lost_reason]["total_pax_days"] += q.get("total_pax_days") or 0
            summary[lost_reason]["total_value"] += q.get("base_grand_total") or 0

    return list(summary.values())


def build_columns(bucket_labels):
    columns = [
        {"label": "Lost Reason", "fieldname": "lost_reason", "fieldtype": "Data", "width": 200},
    ]
    for label in bucket_labels:
        columns.append({"label": label, "fieldname": label, "fieldtype": "Int", "width": 100})
    columns.extend([
        {"label": "Total Quotations", "fieldname": "total_quotations", "fieldtype": "Int", "width": 140},
        {"label": "Total Pax", "fieldname": "total_pax", "fieldtype": "Float", "width": 100},
        {"label": "Total Pax-Days", "fieldname": "total_pax_days", "fieldtype": "Float", "width": 140, "hidden": 1},
        {"label": "Total Value", "fieldname": "total_value", "fieldtype": "Currency", "width": 150, "hidden": 1},
    ])
    return columns


def get_bucket_labels(limits):
    labels = []
    start = 1
    for limit in limits:
        labels.append(f"{start}-{limit}")
        start = limit + 1
    labels.append(f"{start}+")
    return labels


def get_ageing_bucket(value, limits):
    if not limits:
        return "N/A"

    start = 1
    for limit in limits:
        if value <= limit:
            return f"{start}-{limit}"
        start = limit + 1
    return f"{start}+"
