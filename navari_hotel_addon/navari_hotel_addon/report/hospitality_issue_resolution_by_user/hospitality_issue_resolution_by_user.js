// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Hospitality Issue Resolution by User"] = {
  filters: [
    {
      fieldname: "company",
      label: "Company",
      fieldtype: "Link",
      options: "Company",
    },
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date",
      default: "Today",
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date",
      default: "Today",
      reqd: 1,
    },
    {
      fieldname: "department",
      label: "Department",
      fieldtype: "Link",
      options: "Department",
    },
    {
      fieldname: "location",
      label: "Location",
      fieldtype: "Link",
      options: "Location",
    },
    {
      fieldname: "issue_type",
      label: "Issue Type",
      fieldtype: "Link",
      options: "Issue Type",
    },
  ],
};
