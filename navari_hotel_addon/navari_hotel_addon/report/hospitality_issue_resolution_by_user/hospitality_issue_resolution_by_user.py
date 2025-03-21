# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _


def execute(filters=None):
    return HospitalityIssueResolutionByUser(filters).run()

class HospitalityIssueResolutionByUser:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.data = []
        self.columns = []
        self.chart = None
        self.report_summary = []
        self.filtered_issues = []

    def run(self):
        self.get_columns()
        self.get_data()
        self.get_chart_data()
        self.get_report_summary()
        return self.columns, self.data, None, self.chart, self.report_summary

    def get_columns(self):
        self.columns = [
            {"label": _("User"), "fieldname": "user_link", "fieldtype": "Data", "width": 260},
            {"label": _("Opened"), "fieldname": "opened", "fieldtype": "Int", "width": 100},
            {"label": _("Assigned"), "fieldname": "assigned", "fieldtype": "Int", "width": 100},
            {"label": _("Replied"), "fieldname": "replied", "fieldtype": "Int", "width": 100},
            {"label": _("Put on Hold"), "fieldname": "on_hold", "fieldtype": "Int", "width": 120},
            {"label": _("Resolved"), "fieldname": "resolved", "fieldtype": "Int", "width": 100},
            {"label": _("Closed"), "fieldname": "closed", "fieldtype": "Int", "width": 100},
            {"label": _("Resolved + Closed"), "fieldname": "resolved_closed", "fieldtype": "Int", "width": 180},
            {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 100},
        ]

    def get_data(self):
        issue_filters = self.build_issue_filters()
        self.filtered_issues = frappe.get_all("Issue", filters=issue_filters, fields=["name", "owner", "_assign"])
        user_stats = self.initialize_user_stats(self.filtered_issues)
        self.aggregate_status_changes(user_stats)
        self.finalize_data(user_stats)

    def build_issue_filters(self):
        filters = []
        f = self.filters
        if f.get("from_date"):
            filters.append(["Issue", "creation", ">=", f["from_date"]])
        if f.get("to_date"):
            filters.append(["Issue", "creation", "<=", f["to_date"]])
        if f.get("location"):
            filters.append(["Issue", "location", "=", f["location"]])
        if f.get("department"):
            filters.append(["Issue", "department", "=", f["department"]])
        if f.get("issue_type"):
            filters.append(["Issue", "issue_type", "=", f["issue_type"]])
        if f.get("company"):
            filters.append(["Issue", "company", "=", f["company"]])
        return filters

    def initialize_user_stats(self, issues):
        stats = {}
        for issue in issues:
            owner = issue.owner
            if owner not in stats:
                stats[owner] = self.init_user_row(owner)
            stats[owner]["opened"] += 1

            if issue._assign:
                try:
                    assigned_users = json.loads(issue._assign)
                    for assigned_user in assigned_users:
                        if assigned_user not in stats:
                            stats[assigned_user] = self.init_user_row(assigned_user)
                        stats[assigned_user]["assigned"] += 1
                except (json.JSONDecodeError, TypeError):
                    pass  
        return stats

    def aggregate_status_changes(self, user_stats):
        for issue in self.filtered_issues:
            versions = frappe.db.get_all("Version",
                filters={"ref_doctype": "Issue", "docname": issue.name},
                fields=["owner", "data"])

            for version in versions:
                try:
                    data_json = json.loads(version.data or "{}")
                except (json.JSONDecodeError, TypeError):
                    continue

                changed_fields = data_json.get("changed", [])
                for field in changed_fields:
                    if field[0] == "status":
                        new_status = field[2]
                        user = version.owner
                        if user not in user_stats:
                            user_stats[user] = self.init_user_row(user)

                        if new_status == "Replied":
                            user_stats[user]["replied"] += 1
                        elif new_status == "On Hold":
                            user_stats[user]["on_hold"] += 1
                        elif new_status == "Resolved":
                            user_stats[user]["resolved"] += 1
                        elif new_status == "Closed":
                            user_stats[user]["closed"] += 1

    def finalize_data(self, user_stats):
        self.data = []
        for user, stats in user_stats.items():
            full_name = frappe.db.get_value("User", user, "full_name") or user
            stats["user_link"] = f'<a href="/app/user/{user}" target="_blank">{full_name}</a>'
            stats["resolved_closed"] = stats["resolved"] + stats["closed"]
            stats["total"] = (
                stats["opened"] + stats["assigned"] + stats["replied"] +
                stats["on_hold"] + stats["resolved"] + stats["closed"]
            )
            self.data.append(stats)


    def init_user_row(self, user):
        return {
            "user": user,
            "opened": 0,
            "assigned": 0,
            "replied": 0,
            "on_hold": 0,
            "resolved": 0,
            "closed": 0,
            "resolved_closed": 0,
            "total": 0,
        }

    def get_chart_data(self):
        if not self.data:
            self.chart = None
            return

        chart_data_map = frappe._dict()
        for entry in self.data:
            user = entry.get("user")
            if user:
                if user not in chart_data_map:
                    chart_data_map[user] = {
                        "open_count": 0,
                        "replied": 0,
                        "on_hold": 0,
                        "resolved": 0,
                        "closed": 0
                    }
                chart_data_map[user]["open_count"] += int(entry.get("opened") or 0)
                chart_data_map[user]["replied"] += int(entry.get("replied") or 0)
                chart_data_map[user]["on_hold"] += int(entry.get("on_hold") or 0)
                chart_data_map[user]["resolved"] += int(entry.get("resolved") or 0)
                chart_data_map[user]["closed"] += int(entry.get("closed") or 0)

        labels = []
        open_issues = []
        replied_issues = []
        on_hold_issues = []
        resolved_issues = []
        closed_issues = []

        for user in list(chart_data_map.keys())[:30]:
            labels.append(user)
            open_issues.append(chart_data_map[user]["open_count"])
            replied_issues.append(chart_data_map[user]["replied"])
            on_hold_issues.append(chart_data_map[user]["on_hold"])
            resolved_issues.append(chart_data_map[user]["resolved"])
            closed_issues.append(chart_data_map[user]["closed"])

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
            open_issues += int(entry.get("opened") or 0)
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
        
        