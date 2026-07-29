frappe.query_reports["Employee Salary Log History"] = {
    filters: [
        {
            fieldname: "company",
            label:     __("Company"),
            fieldtype: "Link",
            options:   "Company",
            default:   frappe.defaults.get_user_default("Company"),
            reqd:      0,
        },
        {
            fieldname: "employee",
            label:     __("Employee"),
            fieldtype: "Link",
            options:   "Employee",
        },
        {
            fieldname: "department",
            label:     __("Department"),
            fieldtype: "Link",
            options:   "Department",
        },
        {
            fieldname: "from_date",
            label:     __("From Date"),
            fieldtype: "Date",
            default:   frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        {
            fieldname: "to_date",
            label:     __("To Date"),
            fieldtype: "Date",
            default:   frappe.datetime.get_today(),
        },
        {
            fieldname: "change_type",
            label:     __("Change Type"),
            fieldtype: "Select",
            options:   "\nAdded\nChanged\nRemoved",
        },
        {
            fieldname: "is_current",
            label:     __("Current Only"),
            fieldtype: "Check",
            default:   0,
        },
    ],

    // Colour-code the Change Type column in the detail table
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "change_type" && data) {
            const colors = {
                "Added":   "green",
                "Changed": "orange",
                "Removed": "red",
            };
            const color = colors[data.change_type];
            if (color) {
                value = `<span style="color:${color}; font-weight:600;">${data.change_type}</span>`;
            }
        }
        if (column.fieldname === "is_active" && data) {
            value = data.is_active
                ? `<span style="color:green;">&#10003;</span>`
                : `<span style="color:#aaa;">&#8722;</span>`;
        }
        return value;
    },
};
