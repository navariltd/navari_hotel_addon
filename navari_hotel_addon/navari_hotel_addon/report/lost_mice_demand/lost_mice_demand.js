// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Lost MICE Demand"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "User"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "customer_group",
            "label": __("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group"
        },
        {
            "fieldname": "lost_reason",
            "label": __("Lost Reason"),
            "fieldtype": "Link",
            "options": "Lost Reason Detail"
        },
        {
            "fieldname": "ageing_buckets",
            "label": __("Ageing Buckets"),
            "fieldtype": "Data",
			"default": "20,80",
            "description": "Comma separated numbers, e.g., 20,80 will result in 20,80,81+"
        },
        {
            "fieldname": "measure_by",
            "label": __("Measure By"),
            "fieldtype": "Select",
            "options": ["Pax", "Pax-Days"],
            "default": "Pax",
			"hidden": 1
        }
    ],
};
