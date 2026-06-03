frappe.query_reports["Workforce Time Audit Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname": "work_type",
			"label": __("Work Type"),
			"fieldtype": "Select",
			"options": [
				"",
				"Working Day Only",
				"Off Day Only",
				"Has OT",
				"Has Shortage",
				"Has Rejection"
			],
			"default": ""
		},
		{
			"fieldname": "eapb_ref",
			"label": __("Bulk Reference"),
			"fieldtype": "Link",
			"options": "Employee Attendance Process Bulk"
		},
		{
			"fieldname": "trial",
			"label": __("Include Draft (Trial)"),
			"fieldtype": "Check",
			"default": 0,
			"description": __("Check to include Draft (unsubmitted) records for review before submission.")
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// Status badge
		if (column.fieldname === "status") {
			if (data.status === "Draft") {
				value = `<span class="indicator-pill orange">${data.status}</span>`;
			} else {
				value = `<span class="indicator-pill green">${data.status}</span>`;
			}
		}

		// Ceiling utilization color
		if (column.fieldname === "wd_ceiling_utilization" || column.fieldname === "od_ceiling_utilization") {
			let util = flt(data[column.fieldname]);
			if (util > 0) {
				let color = util >= 95 ? "red" : util >= 80 ? "orange" : "green";
				value = `<span style="color: var(--${color}-500); font-weight: 600;">${util.toFixed(1)}%</span>`;
			}
		}

		// OT Approval Rate color
		if (column.fieldname === "ot_approval_rate" && data.ot_approval_rate != null) {
			let rate = flt(data.ot_approval_rate);
			let color = rate >= 90 ? "green" : rate >= 70 ? "orange" : "red";
			value = `<span style="color: var(--${color}-500); font-weight: 600;">${rate.toFixed(1)}%</span>`;
		}

		// Rejected hours — highlight if > 0
		if ((column.fieldname === "rejected_ot_wd_hours" || column.fieldname === "rejected_ot_od_hours") &&
			flt(data[column.fieldname]) > 0) {
			value = `<span style="color: var(--red-500);">${value}</span>`;
		}

		// Shortage reduced — highlight if > 0
		if (column.fieldname === "shortage_reduced_hours" && flt(data.shortage_reduced_hours) > 0) {
			value = `<span style="color: var(--blue-500);">${value}</span>`;
		}

		// Savings columns — bold if positive
		if (["wd_ot_savings", "od_ot_savings", "total_ot_savings", "shortage_savings"].includes(column.fieldname)) {
			if (flt(data[column.fieldname]) > 0) {
				value = `<strong>${value}</strong>`;
			}
		}

		return value;
	},

	"initial_depth": 0
};
