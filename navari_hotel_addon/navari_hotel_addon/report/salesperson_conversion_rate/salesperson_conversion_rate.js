// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Salesperson Conversion Rate"] = {
	"filters": [
		{
			"fieldname": "sales_person",
			"label": "Sales Person",
			"fieldtype": "Link",
			"options": "Sales Person",
			"reqd": 0
		},
		{
			"fieldname": "period",
			"label": "Period",
			"fieldtype": "Select",
			"options": "\nThis Week\nLast Week\nThis Month\nLast Month\nThis Year\nLast Year\nCustom",
			"default": "This Month",
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"depends_on": "eval:doc.period === 'Custom'",
			"reqd": 0
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"depends_on": "eval:doc.period === 'Custom'",
			"reqd": 0
		}
  	]
};
