frappe.query_reports["Department Overtime Analysis"] = {
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
    ],

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "approval_rate" && data) {
            const rate = data.approval_rate || 0;
            let color = "#28a745";
            if (rate < 50) color = "#dc3545";
            else if (rate < 75) color = "#fd7e14";
            value = `<span style="color:${color}; font-weight:600;">${rate.toFixed(2)}%</span>`;
        }

        return value;
    },
};
