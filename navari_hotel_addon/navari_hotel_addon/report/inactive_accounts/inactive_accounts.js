// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Inactive Accounts"] = {
  filters: [
    {
      fieldname: "customer",
      label: __("Search Customer"),
      fieldtype: "Link",
      options: "Customer",
    },
    {
      fieldname: "doctype",
      label: __("Doctype"),
      fieldtype: "Select",
      default: "Last Activity (All)",
      options: "Last Activity (All)\nQuotation\nSales Order\nSales Invoice",
      description: __(
        "Select a single doctype or choose 'Last Activity (All)' to check across all"
      ),
    },
    {
      fieldname: "last_order_period",
      label: "Last Order Period",
      fieldtype: "Select",
      options: "\nAll\nLast Week\nLast Month\nLast Year",
      default: "All",
    },
    {
      fieldname: "last_order_from",
      label: "From Date",
      fieldtype: "Date",
    },
    {
      fieldname: "last_order_to",
      label: "To Date",
      fieldtype: "Date",
    },
  ],
};
