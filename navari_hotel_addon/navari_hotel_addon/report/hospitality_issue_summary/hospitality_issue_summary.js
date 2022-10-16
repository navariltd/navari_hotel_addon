// Copyright (c) 2022, Navari Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Hospitality Issue Summary"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "based_on",
			label: __("Based On"),
			fieldtype: "Select",
			options: ["", "Location", "Department", "Issue Type", "Asset", "Issue Priority", "Assigned To"],
			default: "Department",
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_global_default("year_start_date"),
			reqd: 1
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_global_default("year_end_date"),
			reqd: 1
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options:[
				"",
				{label: __('Open'), value: 'Open'},
				{label: __('Replied'), value: 'Replied'},
				{label: __('On Hold'), value: 'On Hold'},
				{label: __('Resolved'), value: 'Resolved'},
				{label: __('Closed'), value: 'Closed'}
			]
		},
		{
			fieldname: "location",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location"
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department"
		},
		{
			fieldname: "issue_type",
			label: __("Issue Type"),
			fieldtype: "Link",
			options: "Issue Type"
		},
		{
			fieldname: "asset",
			label: __("Asset"),
			fieldtype: "Link",
			options: "Asset"
		},
		{
			fieldname: "priority",
			label: __("Issue Priority"),
			fieldtype: "Link",
			options: "Issue Priority"
		},
		{
			fieldname: "assigned_to",
			label: __("Assigned To"),
			fieldtype: "Link",
			options: "User"
		}
	]
};
