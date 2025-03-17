# Copyright (c) 2024, Navari Limited and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _, scrub
from frappe.utils import flt
from six import iteritems

def execute(filters=None):
    return HospitalityIssueResolutionByUser(filters).run()

class HospitalityIssueResolutionByUser:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.base_field = {
            "Location": "location",
            "Department": "department",
            "Issue Type": "issue_type",
            "Asset": "asset",
            "Issue Priority": "priority"
        }.get(self.filters.get("based_on"), "department")  
        self.data = []
        self.columns = []
        self.chart = None

    def run(self):
        self.get_columns()
        self.get_data()
        self.get_chart_data()
        self.get_report_summary()
        return self.columns, self.data, None, self.chart, self.report_summary

    def get_columns(self):
        self.columns = [{
            "label": _(self.filters.based_on),
            "fieldname": scrub(self.filters.based_on),
            "fieldtype": "Link",
            "options": self.filters.based_on,
            "width": 200
        }]
        self.columns.extend([
            {"label": _("Total Opened"), "fieldname": "total_opened", "fieldtype": "Data", "width": 120},
            {"label": _("Open"), "fieldname": "open_count", "fieldtype": "Data", "width": 100},
        ])
        self.columns.append({"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Data", "width": 200})
        for status in ["Replied", "On Hold", "Resolved", "Closed"]:
            self.columns.append({"label": _(status), "fieldname": scrub(status), "fieldtype": "Int", "width": 100})
        self.columns.extend([
            {"label": _("Resolved + Closed"), "fieldname": "resolved_closed", "fieldtype": "Int", "width": 140},
            {"label": _("User Total"), "fieldname": "user_total", "fieldtype": "Int", "width": 120},
        ])

    def get_filtered_issues(self):
        filters = {
            "opening_date": ["between", [self.filters.from_date, self.filters.to_date]],
        }
        for key in ["company", "status", "location", "department", "issue_type", "asset", "priority"]:
            if self.filters.get(key):
                filters[key] = self.filters.get(key)
        if self.filters.get("assigned_to"):
            filters["_assign"] = ("like", f"%{self.filters.get('assigned_to')}%")
        fields = [self.base_field, "_assign", "status"]
        return frappe.db.get_all("Issue", filters=filters, fields=fields)

    def get_all_base_values(self):
        if self.base_field == "location":
            return frappe.get_all("Location", pluck="name")
        elif self.base_field == "department":
            return frappe.get_all("Department", pluck="name")
        elif self.base_field == "issue_type":
            return frappe.get_all("Issue Type", pluck="name")
        elif self.base_field == "asset":
            return frappe.get_all("Asset", pluck="name")
        elif self.base_field == "priority":
            return frappe.get_all("Issue Priority", pluck="name")
        else:
            return []

    def get_data(self):
        issues = self.get_filtered_issues()
        all_base_values = self.get_all_base_values()
        summary_map = frappe._dict()
        for issue in issues:
            base_value = issue.get(self.base_field) or _("Not Specified")
            summary_map.setdefault(base_value, {
                "total_opened": 0,
                "open_count": 0,
                "replied": 0,
                "on_hold": 0,
                "resolved": 0,
                "closed": 0,
                "users": frappe._dict()
            })
            summary_map[base_value]["total_opened"] += 1
            if issue.status == "Open":
                summary_map[base_value]["open_count"] += 1
            elif issue.status == "Replied":
                summary_map[base_value]["replied"] += 1
            elif issue.status == "On Hold":
                summary_map[base_value]["on_hold"] += 1
            elif issue.status == "Resolved":
                summary_map[base_value]["resolved"] += 1
            elif issue.status == "Closed":
                summary_map[base_value]["closed"] += 1
            if issue._assign:
                assigned_users = json.loads(issue._assign)
                if self.filters.get("assigned_to"):
                    if self.filters.get("assigned_to") in assigned_users:
                        user_data = summary_map[base_value]["users"].setdefault(self.filters.get("assigned_to"), {
                            "Replied": 0,
                            "On Hold": 0,
                            "Resolved": 0,
                            "Closed": 0,
                            "user_total": 0
                        })
                        if issue.status in user_data:
                            user_data[issue.status] += 1
                        user_data["user_total"] += 1
                else:
                    for user in assigned_users:
                        user_data = summary_map[base_value]["users"].setdefault(user, {
                            "Replied": 0,
                            "On Hold": 0,
                            "Resolved": 0,
                            "Closed": 0,
                            "user_total": 0
                        })
                        if issue.status in user_data:
                            user_data[issue.status] += 1
                        user_data["user_total"] += 1
        for base_value in all_base_values:
            base_entry = summary_map.get(base_value, {
                "total_opened": 0,
                "open_count": 0,
                "replied": 0,
                "on_hold": 0,
                "resolved": 0,
                "closed": 0,
                "users": {}
            })
            if base_entry["total_opened"] == 0:
                continue
            self.data.append({
                scrub(self.filters.based_on): base_value,
                "total_opened": base_entry["total_opened"],
                "open_count": base_entry["open_count"],
                "replied": base_entry["replied"],
                "on_hold": base_entry["on_hold"],
                "resolved": base_entry["resolved"],
                "closed": base_entry["closed"],
                "resolved_closed": base_entry["resolved"] + base_entry["closed"],
                "assigned_to": "",
                "user_total": 0
            })
            for user, user_data in base_entry["users"].items():
                user_fullname = frappe.get_value("User", user, "full_name")
                row = {
                    scrub(self.filters.based_on): "",
                    "total_opened": "",
                    "open_count": "",
                    "assigned_to": f'<a href="/app/user/{user}">{user_fullname}</a>',
                    "replied": user_data.get("Replied", 0),
                    "on_hold": user_data.get("On Hold", 0),
                    "resolved": user_data.get("Resolved", 0),
                    "closed": user_data.get("Closed", 0),
                    "resolved_closed": user_data.get("Resolved", 0) + user_data.get("Closed", 0),
                    "user_total": user_data.get("user_total", 0)
                }
                self.data.append(row)

    def get_chart_data(self):
        chart_data_map = frappe._dict()
        for entry in self.data:
            base_value = entry.get(scrub(self.filters.based_on))
            if base_value:
                if base_value not in chart_data_map:
                    chart_data_map[base_value] = {
                        "open_count": 0,
                        "replied": 0,
                        "on_hold": 0,
                        "resolved": 0,
                        "closed": 0
                    }
                chart_data_map[base_value]["open_count"] += int(entry.get("open_count") or 0)
                chart_data_map[base_value]["replied"] += int(entry.get("replied") or 0)
                chart_data_map[base_value]["on_hold"] += int(entry.get("on_hold") or 0)
                chart_data_map[base_value]["resolved"] += int(entry.get("resolved") or 0)
                chart_data_map[base_value]["closed"] += int(entry.get("closed") or 0)
        labels = []
        open_issues = []
        replied_issues = []
        on_hold_issues = []
        resolved_issues = []
        closed_issues = []
        for base_value in list(chart_data_map.keys())[:30]:
            labels.append(base_value)
            open_issues.append(chart_data_map[base_value]["open_count"])
            replied_issues.append(chart_data_map[base_value]["replied"])
            on_hold_issues.append(chart_data_map[base_value]["on_hold"])
            resolved_issues.append(chart_data_map[base_value]["resolved"])
            closed_issues.append(chart_data_map[base_value]["closed"])
        self.chart = {
            "data": {
                "labels": labels,
                "datasets": [
                    {"name": "Open", "values": open_issues},
                    {"name": "Replied", "values": replied_issues},
                    {"name": "On Hold", "values": on_hold_issues},
                    {"name": "Resolved", "values": resolved_issues},
                    {"name": "Closed", "values": closed_issues},
                ],
            },
            "type": "bar",
            "barOptions": {"stacked": True},
        }

    def get_report_summary(self):
        self.report_summary = []
        open_issues = 0
        replied = 0
        on_hold = 0
        resolved = 0
        closed = 0
        for entry in self.data:
            open_issues += int(entry.get("open_count") or 0)
            replied += int(entry.get("replied") or 0)
            on_hold += int(entry.get("on_hold") or 0)
            resolved += int(entry.get("resolved") or 0)
            closed += int(entry.get("closed") or 0)
        self.report_summary = [
            {
                "value": open_issues,
                "indicator": "Red",
                "label": _("Open"),
                "datatype": "Int",
            },
            {
                "value": replied,
                "indicator": "Grey",
                "label": _("Replied"),
                "datatype": "Int",
            },
            {
                "value": on_hold,
                "indicator": "Grey",
                "label": _("On Hold"),
                "datatype": "Int",
            },
            {
                "value": resolved,
                "indicator": "Green",
                "label": _("Resolved"),
                "datatype": "Int",
            },
            {
                "value": closed,
                "indicator": "Green",
                "label": _("Closed"),
                "datatype": "Int",
            },
        ]
