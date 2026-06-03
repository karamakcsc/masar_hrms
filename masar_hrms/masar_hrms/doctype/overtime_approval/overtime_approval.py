import frappe
from frappe.model.document import Document
from frappe.utils import flt


class OvertimeApproval(Document):

	def validate(self):
		self._validate_no_duplicate_dates()
		self._validate_approved_hours()
		self._check_conflicts()

	def _validate_no_duplicate_dates(self):
		seen = set()
		for row in self.overtime_details:
			if row.date in seen:
				frappe.throw(
					frappe._("Duplicate date {0} in row {1}.").format(row.date, row.idx)
				)
			seen.add(row.date)

	def _validate_approved_hours(self):
		for row in self.overtime_details:
			if flt(row.approved_hours) <= 0:
				frappe.throw(
					frappe._("Row {0}: Approved Overtime Hours must be greater than zero.").format(row.idx)
				)

	def _check_conflicts(self):
		"""Ensure no submitted OTA already covers the same employee + date."""
		dates = [row.date for row in self.overtime_details if row.date]
		if not dates:
			return
		conflicts = frappe.db.sql("""
			SELECT oad.date, oa.name
			FROM `tabOvertime Approval Detail` oad
			INNER JOIN `tabOvertime Approval` oa ON oa.name = oad.parent
			WHERE oa.employee = %(employee)s
				AND oa.docstatus = 1
				AND oa.name != %(name)s
				AND oad.date IN %(dates)s
			LIMIT 1
		""", {
			'employee': self.employee,
			'name': self.name or '',
			'dates': dates
		}, as_dict=True)
		if conflicts:
			frappe.throw(
				frappe._(
					"A submitted Overtime Approval ({0}) already exists for employee {1} on {2}."
				).format(conflicts[0].name, self.employee, conflicts[0].date)
			)

	def on_submit(self):
		self.db_set('status', 'Approved')

	def on_cancel(self):
		self.db_set('status', 'Cancelled')
