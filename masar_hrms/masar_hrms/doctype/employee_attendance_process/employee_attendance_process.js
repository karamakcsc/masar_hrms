// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Attendance Process", {
	employee: function(frm) {
		GetSalaryDetailsForEmployee(frm);
		GetOvertimeTypeAsDefault(frm);
	},
	posting_date: function(frm) {
		GetStandardDatePeriod(frm);
	},
	refresh: function(frm) {
		GetStandardDatePeriod(frm);
		GetOvertimeTypeAsDefault(frm);
		setupChildTableRestrictions(frm);
	},
	setup: function(frm) {
		GetStandardDatePeriod(frm);
		GetOvertimeTypeAsDefault(frm);
	},
	onload: function(frm) {
		GetStandardDatePeriod(frm);
		GetOvertimeTypeAsDefault(frm);
	},
});

// When HR edits approved overtime, mark row as manually adjusted
frappe.ui.form.on("EAP Overtime Detail", {
	overtime: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let calc = row.calculated_overtime || 0;
		if (row.overtime > calc) {
			frappe.model.set_value(cdt, cdn, 'overtime', calc);
			frappe.msgprint(__('Approved Overtime cannot exceed Calculated Overtime ({0}).', [
				frappe.utils.get_formatted_duration(calc)
			]));
			return;
		}
		frappe.model.set_value(cdt, cdn, 'is_manually_adjusted', 1);
	}
});

// When HR edits approved shortage, validate it does not exceed calculated and recalculate amounts
frappe.ui.form.on("EAP Leave Detail", {
	approved_shortage: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let calc = row.total_shortage || 0;
		if (row.approved_shortage > calc) {
			frappe.model.set_value(cdt, cdn, 'approved_shortage', calc);
			frappe.msgprint(__('Approved Shortage cannot exceed Calculated Shortage ({0}).', [
				frappe.utils.get_formatted_duration(calc)
			]));
			return;
		}

		// Recalculate row amount based on new approved_shortage
		let hour_rate = frm.doc.shortage_hour_rate || 0;
		let approved = flt(row.approved_shortage) || 0;
		let new_amount = (approved / 3600) * hour_rate;
		frappe.model.set_value(cdt, cdn, 'amount', new_amount);

		// Recalculate parent total_shortage_amount
		let total_amount = 0;
		(frm.doc.leaves || []).forEach(function(r) {
			total_amount += flt(r.amount) || 0;
		});
		frm.set_value('total_shortage_amount', total_amount);
	}
});

function setupChildTableRestrictions(frm) {
	// Prevent HR from adding or deleting rows manually
	if (frm.fields_dict.overtime_table && frm.fields_dict.overtime_table.grid) {
		frm.fields_dict.overtime_table.grid.cannot_add_rows = true;
		frm.fields_dict.overtime_table.grid.cannot_delete_rows = true;
	}
	if (frm.fields_dict.leaves && frm.fields_dict.leaves.grid) {
		frm.fields_dict.leaves.grid.cannot_add_rows = true;
		frm.fields_dict.leaves.grid.cannot_delete_rows = true;
	}
}

function GetSalaryDetailsForEmployee(frm) {
	frappe.call({
		doc: frm.doc,
		method: 'get_salary_details',
		args: { employee: frm.doc.employee },
		callback: function(r) {
			frm.set_value('basic_salary', r.message.basic_salary);
			frm.set_value('basic_salary_hour_rate', r.message.hour_rate);
			frm.set_value('shortage_hour_rate', r.message.shortage_hour_rate);
			frm.set_value('earning_salary', r.message.earning_salary);
		}
	});
}

function GetStandardDatePeriod(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'get_standard_date_period',
			callback: function(r) {
				if (r.message) {
					frm.set_value('from_date', r.message.from_date);
					frm.set_value('to_date', r.message.to_date);
				}
			}
		});
}

function GetOvertimeTypeAsDefault(frm) {
	frappe.call({
		doc: frm.doc,
		method: 'get_overtime_type_as_defualt',
		callback: function(r) {
			frm.set_value('ot_wd', r.message.ot_wd);
			frm.set_value('salary_component_wd', r.message.salary_component_wd);
			frm.set_value('ot_wd_rate', r.message.ot_wd_rate);
			frm.set_value('ot_od', r.message.ot_od);
			frm.set_value('salary_component_od', r.message.salary_component_od);
			frm.set_value('ot_od_rate', r.message.ot_od_rate);
		}
	});
}
