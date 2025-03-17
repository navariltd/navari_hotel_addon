// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Hospitality Issue Resolution by User"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "based_on",
      label: __("Based On"),
      fieldtype: "Select",
      options: [
        "",
        "Location",
        "Department",
        "Issue Type",
        "Asset",
        "Issue Priority",
      ],
      default: "Issue Type",
      reqd: 1,
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.defaults.get_global_default("year_start_date"),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.defaults.get_global_default("year_end_date"),
      reqd: 1,
    },
    {
      fieldname: "location",
      label: __("Location"),
      fieldtype: "Link",
      options: "Location",
    },
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
    },
    {
      fieldname: "issue_type",
      label: __("Issue Type"),
      fieldtype: "Link",
      options: "Issue Type",
    },
    {
      fieldname: "asset",
      label: __("Asset"),
      fieldtype: "Link",
      options: "Asset",
    },
    {
      fieldname: "priority",
      label: __("Issue Priority"),
      fieldtype: "Link",
      options: "Issue Priority",
    },
    {
      fieldname: "assigned_to",
      label: __("Assigned To"),
      fieldtype: "Link",
      options: "User",
    },
  ],
};
