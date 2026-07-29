// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Social Security - Active"] = {
    "filters": [
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 100,
        },
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Int",
            "width": 80,
            "default": frappe.datetime.get_today().split("-")[0] 
        },
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
            "width": 100,
            "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).toLocaleString('default', { month: 'long' })
        },
        {
            "fieldname": "damman_template",
            "label": __("Damman Template"),
            "fieldtype": "Check",
            "default": 0
        }
    ]
};

