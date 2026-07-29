frappe.query_reports["Overtime Rejection Analysis"] = {
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

        if (column.fieldname === "ot_type" && data) {
            const color = data.ot_type === "Off Day" ? "#6f42c1" : "#0d6efd";
            value = `<span style="color:${color}; font-weight:600;">${data.ot_type}</span>`;
        }

        if (column.fieldname === "rejection_pct" && data) {
            const pct = data.rejection_pct || 0;
            let color = "#28a745";
            if (pct >= 75) color = "#dc3545";
            else if (pct >= 50) color = "#fd7e14";
            else if (pct > 0) color = "#ffc107";
            value = `<span style="color:${color}; font-weight:600;">${pct.toFixed(2)}%</span>`;
        }

        if (column.fieldname === "rejected_hours" && data) {
            const hrs = data.rejected_hours || 0;
            if (hrs > 0) {
                value = `<span style="color:#dc3545; font-weight:600;">${hrs.toFixed(2)}</span>`;
            }
        }

        return value;
    },
};
