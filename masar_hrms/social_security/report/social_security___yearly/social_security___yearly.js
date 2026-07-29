// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Social Security - Yearly"] = {
    "filters": [
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "width": 80,
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 100,
        },
		{
            "fieldname": "damman_template",
            "label": __("Damman Template"),
            "fieldtype": "Check",
            "default": 0
        },
    ]
};
