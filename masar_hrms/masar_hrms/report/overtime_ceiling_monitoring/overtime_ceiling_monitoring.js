frappe.query_reports["Overtime Ceiling Monitoring"] = {
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

        if (column.fieldname === "indicator" && data) {
            const colorMap = {
                "Red":    "#dc3545",
                "Orange": "#fd7e14",
                "Green":  "#28a745",
            };
            const color = colorMap[data.indicator] || "#6c757d";
            const dot = `<span style="
                display:inline-block;
                width:10px; height:10px;
                border-radius:50%;
                background:${color};
                margin-right:6px;
                vertical-align:middle;
            "></span>`;
            value = `${dot}<span style="color:${color}; font-weight:600;">${data.indicator || ""}</span>`;
        }

        if (["wd_utilization", "od_utilization"].includes(column.fieldname) && data) {
            const util = data[column.fieldname];
            if (util !== null && util !== undefined) {
                let color = "#28a745";
                if (util >= 95) color = "#dc3545";
                else if (util >= 80) color = "#fd7e14";
                value = `<span style="color:${color}; font-weight:600;">${util.toFixed(1)}%</span>`;
            }
        }

        return value;
    },
};
