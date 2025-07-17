// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Inactive Accounts"] = {
	"filters": [
		{
			"fieldname": "doctype",
			"label": __("Doctype"),
			"fieldtype": "Select",
			"default": "Quotation",
			"options": "Quotation\nSales Order\nSales Invoice",
		},
		{
			"fieldname": "last_order_period",
			"label": "Last Order Period",
			"fieldtype": "Select",
			"options": "\nAll\nLast Week\nLast Month\nLast Year",
			"default": "All"
		},
		{
			"fieldname": "last_order_from",
			"label": "From Date",
			"fieldtype": "Date"
		},
		{
			"fieldname": "last_order_to",
			"label": "To Date",
			"fieldtype": "Date"
		}
	]
};
