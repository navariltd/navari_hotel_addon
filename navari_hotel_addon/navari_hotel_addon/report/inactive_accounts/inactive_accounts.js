// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Inactive Accounts"] = {
	"filters": [
		{
			"fieldname": "days_since_last_order",
			"label": __("Days Since Last Order"),
			"fieldtype": "Int",
			"default": 60,
		},
		{
			"fieldname": "doctype",
			"label": __("Doctype"),
			"fieldtype": "Select",
			"default": "Quotation",
			"options": "Quotation\nSales Order\nSales Invoice",
		},
	]
};
