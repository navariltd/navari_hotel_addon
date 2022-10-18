# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
from frappe.utils import flt, getdate
from six import iteritems

from frappe.utils.nestedset import get_descendants_of


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	columns = get_columns(filters)
	data = get_data(filters)

	chart_data = get_chart_data(data)

	return columns, data, None, chart_data

def get_columns(filters):
	return [
		{
			"label": _("Reserved Period"),
			"fieldtype": "Data",
			"fieldname": "reserved_period",
			"width": 150
		},
		{
			"label": _("Customer Group"),
			"fieldtype": "Link",
			"fieldname": "customer_group",
			"options": "Customer Group",
			"width": 150
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 200
		},
		{
			"label": _("Sales Order"),
			"fieldtype": "Link",
			"fieldname": "sales_order",
			"options": "Sales Order",
			"width": 130
		},
		{
			"label":_("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Account Manager Name"),
			"fieldtype": "Data",
			"fieldname": "account_manager_name",
			"width": 150
		},
		{
			"label": _("Transaction Date"),
			"fieldtype": "Date",
			"fieldname": "transaction_date",
			"width": 100
		},
		{
			"label": _("Item Group"),
			"fieldtype": "Link",
			"fieldname": "item_group",
			"options": "Item Group",
			"width": 130
		},
		{
			"label": _("Item Code"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options": "Item",
			"width": 220
		},
		{
			"label": _("Reservation Option"),
			"fieldtype": "Select",
			"fieldname": "reservation_option",
			"width": 130
		},
		{
			"label": _("Quantity"),
			"fieldtype": "Float",
			"fieldname": "quantity",
			"width": 80,
			"convertible": "qty"
		},
		{
			"label": _("Start Date"),
			"fieldtype": "Date",
			"fieldname": "start_date",
			"width": 100
		},
		{
			"label": _("End Date"),
			"fieldtype": "Date",
			"fieldname": "end_date",
			"width": 100
		},
		{
			"label": _("Days"),
			"fieldtype": "Float",
			"fieldname": "days",
			"width": 70,
			"convertible": "qty"
		},
		{
			"label": _("Currency"),
			"fieldtype": "Link",
			"fieldname": "currency",
			"options": "Currency",
			"width": 80
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			'fieldtype': 'Float',
			"width": 100,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Base Rate"),
			"fieldname": "base_rate",
			'fieldtype': 'Float',
			"width": 100,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			'fieldtype': 'Currency',
			"width": 120,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Base Amount"),
			"fieldname": "base_amount",
			'fieldtype': 'Currency',
			"width": 120,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Billed Amount"),
			"fieldname": "billed_amount",
			'fieldtype': 'Currency',
			"width": 120,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Company"),
			"fieldtype": "Link",
			"fieldname": "company",
			"options": "Company",
			"width": 100
		}
	]

def get_data(filters):

	data = []

	company_list = get_descendants_of("Company", filters.get("company"))
	company_list.append(filters.get("company"))

	customer_details = get_customer_details()
	item_details = get_item_details()
	sales_order_records = get_sales_order_details(company_list, filters)

	for record in sales_order_records:
		customer_record = customer_details.get(record.customer)
		item_record = item_details.get(record.item_code)
		w_s_date = getdate(record.start_date)
		reserved_period = "Week " + str(w_s_date.isocalendar()[1]) + " " + str(w_s_date.year)
		row = {
			"reserved_period": reserved_period,
			"item_code": record.item_code,
			"item_group": item_record.item_group,
			"reservation_option": record.reservation_option,
			"quantity": flt(record.qty),
			"start_date": record.start_date,
			"end_date": record.end_date,
			"days": flt(record.days),
			"currency": record.currency,
			"rate": flt(record.rate),
			"base_rate": flt(record.base_rate),
			"amount": flt(record.amount),
			"base_amount": flt(record.base_amount),
			"sales_order": record.name,
			"status": record.status,
			"account_manager_name": record.account_manager_name,
			"transaction_date": record.transaction_date,
			"customer": record.customer,
			"customer_group": customer_record.customer_group,
			"billed_amount": flt(record.billed_amt),
			"company": record.company
		}
		data.append(row)

	return data

def get_conditions(filters):
	conditions = ''
	if filters.get('item_group'):
		conditions += "AND so_item.item_group = %s" %frappe.db.escape(filters.item_group)

	if filters.get('from_date'):
		conditions += "AND so_item.start_date >= '%s'" %filters.from_date

	if filters.get('to_date'):
		conditions += "AND so_item.end_date <= '%s'" %filters.to_date

	if filters.get("item_code"):
		conditions += "AND so_item.item_code = %s" %frappe.db.escape(filters.item_code)

	if filters.get('customer_group'):
		conditions += "AND so.customer_group = %s" %frappe.db.escape(filters.customer_group)

	if filters.get("customer"):
		conditions += "AND so.customer = %s" %frappe.db.escape(filters.customer)

	return conditions

def get_customer_details():
	details = frappe.get_all("Customer",
		fields=["name", "customer_group"])
	customer_details = {}
	for d in details:
		customer_details.setdefault(d.name, frappe._dict({
			"customer_group": d.customer_group
		}))
	return customer_details

def get_item_details():
	details = frappe.db.get_all("Item",
		fields=["item_code", "item_group"])
	item_details = {}
	for d in details:
		item_details.setdefault(d.item_code, frappe._dict({
			"item_group": d.item_group
		}))
	return item_details

def get_sales_order_details(company_list, filters):
	conditions = get_conditions(filters)

	return frappe.db.sql("""
		SELECT
			so_item.item_code, so_item.reservation_option, so_item.qty,
			so_item.start_date, so_item.end_date, so_item.days,
			so.currency, so_item.rate, so_item.base_rate, 
			so_item.amount, so_item.base_amount,
			so.name, so.status, so.account_manager_name,
			so.transaction_date, so.customer, so_item.billed_amt, so.company
		FROM
			`tabSales Order` so, `tabSales Order Item` so_item
		WHERE
			so.name = so_item.parent
			AND so.company in ({0})
			AND so.docstatus = 1 {1}
			AND so.status != "Closed"
		ORDER BY so_item.start_date ASC
	""".format(','.join(["%s"] * len(company_list)), conditions), tuple(company_list), as_dict=1)

def get_chart_data(data):
	reserved_period_wise_sales_map = {}
	labels, datapoints = [], []

	for row in data:
		reserved_period_key = row.get("reserved_period")

		if not reserved_period_key in reserved_period_wise_sales_map:
			reserved_period_wise_sales_map[reserved_period_key] = 0

		reserved_period_wise_sales_map[reserved_period_key] = flt(reserved_period_wise_sales_map[reserved_period_key]) + flt(row.get("days"))

	reserved_period_wise_sales_map = { item: value for item, value in (sorted(reserved_period_wise_sales_map.items(), key = lambda i: i[1], reverse=True))}

	for key in reserved_period_wise_sales_map:
		labels.append(key)
		datapoints.append(reserved_period_wise_sales_map[key])

	return {
		"data" : {
			"labels" : labels[:30], # show max of 30 items in chart
			"datasets" : [
				{
					"name" : _(" Reserved Days"),
					"values" : datapoints[:30]
				}
			]
		},
		"type" : "bar"
	}
