frappe.query_reports["Shortage Adjustment Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label:     __("From Date"),
            fieldtype: "Date",
            default:   frappe.datetime.month_start(),
            reqd:      1,
        },
        {
            fieldname: "to_date",
            label:     __("To Date"),
            fieldtype: "Date",
            default:   frappe.datetime.month_end(),
            reqd:      1,
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
    ],

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "difference" && data) {
            const diff = data.difference || 0;
            if (diff > 0) {
                // Calculated > Approved → shortage was reduced (benefit to employee)
                value = `<span style="color:#28a745; font-weight:600;">${diff.toFixed(2)}</span>`;
            } else if (diff < 0) {
                // Approved > Calculated → shortage was increased
                value = `<span style="color:#dc3545; font-weight:600;">${diff.toFixed(2)}</span>`;
            }
        }

        if (column.fieldname === "approved_amount" && data) {
            const amt = data.approved_amount || 0;
            if (amt > 0) {
                value = `<span style="color:#dc3545; font-weight:600;">${format_currency(amt)}</span>`;
            }
        }

        return value;
    },
};
