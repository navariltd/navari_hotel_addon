# Copyright (c) 2025, Navari Limited and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


import frappe
from frappe import _
from frappe.utils import getdate, add_months, add_years, get_first_day, get_last_day, today

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = []

	conditions = []
	args = {}

	today = getdate()
	period = filters.get("period")

	# Resolve date range based on period
	if period and period != "Custom":
		if period == "This Week":
			start = today - timedelta(days=today.weekday())
			end = start + timedelta(days=6)
		elif period == "Last Week":
			start = today - timedelta(days=today.weekday() + 7)
			end = start + timedelta(days=6)
		elif period == "This Month":
			start = get_first_day(today)
			end = get_last_day(today)
		elif period == "Last Month":
			start = add_months(get_first_day(today), -1)
			end = get_last_day(start)
		elif period == "This Year":
			start = getdate(f"{today.year}-01-01")
			end = getdate(f"{today.year}-12-31")
		elif period == "Last Year":
			start = getdate(f"{today.year - 1}-01-01")
			end = getdate(f"{today.year - 1}-12-31")

		filters["from_date"] = start
		filters["to_date"] = end

	# Apply filters
	if filters.get("from_date"):
		conditions.append("q.transaction_date >= %(from_date)s")
		args["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("q.transaction_date <= %(to_date)s")
		args["to_date"] = filters["to_date"]

	if filters.get("sales_person"):
		conditions.append("q.account_manager_name = %(sales_person)s")
		args["sales_person"] = filters["sales_person"]

	# Always apply docstatus filter
	conditions.append("q.docstatus = 1")
	where_clause = "WHERE " + " AND ".join(conditions)

	query = f"""
		SELECT
			q.account_manager_name AS sales_person,
			q.account_manager_email,
			COUNT(q.name) AS total_quotations,
			SUM(CASE WHEN q.status IN ('Ordered', 'Partially Ordered') THEN 1 ELSE 0 END) AS converted
		FROM `tabQuotation` q
		{where_clause}
		GROUP BY q.account_manager_email
		ORDER BY q.account_manager_name
	"""

	rows = frappe.db.sql(query, args, as_dict=True)

	for row in rows:
		conversion_rate = (row.converted / row.total_quotations) * 100 if row.total_quotations else 0
		data.append([
			row.sales_person,
			row.total_quotations,
			row.converted,
			round(conversion_rate, 2)
		])

	return columns, data


def get_columns():
	return [
		_("Sales Person") + ":Link/Sales Person:200",
		_("Total Quotations") + ":Int:150",
		_("Converted to Sales Order") + ":Int:180",
		_("Conversion Rate (%)") + ":Percent:150",
	]
