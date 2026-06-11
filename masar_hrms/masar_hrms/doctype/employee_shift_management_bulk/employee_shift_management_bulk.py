# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_weekday, add_days, formatdate
from frappe import db, enqueue, msgprint, _, qb
from datetime import timedelta


class EmployeeShiftManagementBulk(Document):
	@frappe.whitelist()
	def get_day_by_date(self, date=None):
		if date is None:
			return None
		date_obj = getdate(date)
		day_name = get_weekday(date_obj)
		return day_name

	@frappe.whitelist()
	def insert_shifts_periods(self):
		if not (self.start_date and self.end_date):
			frappe.throw("Start Date and End Date are required")

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		if start_date > end_date:
			frappe.throw("End Date cannot be before Start Date")

		self.set("shifts_period", [])

		weekday_field_map = {
			0: "monday_st",
			1: "tuesday_st",
			2: "wednesday_st",
			3: "thursday_st",
			4: "friday_st",
			5: "saturday_st",
			6: "sunday_st"
		}
		current_date = start_date
		while current_date <= end_date:
			weekday = current_date.weekday()
			shift_field = weekday_field_map.get(weekday)
			if shift_field:
				shift_type = self.get(shift_field)
				if shift_type:
					self.append("shifts_period", {
						"shift_date": current_date,
						"shift_day": current_date.strftime("%A"),
						"shift_type": shift_type,
						"start_time": db.get_value('Shift Type', shift_type, 'start_time'),
						"end_time": db.get_value('Shift Type', shift_type, 'end_time')
					})
			current_date = add_days(current_date, 1)
		msg = f"Created {len(self.shifts_period)} shift period(s) between {formatdate(self.start_date)} and {formatdate(self.end_date)}"
		msgprint(msg, alert=True, indicator='green')

	@frappe.whitelist()
	def insert_employees(self, advanced_filters: list | None = None):
		if not advanced_filters:
			advanced_filters = []
		e = qb.DocType("Employee")
		q = (
			qb.from_(e).select(e.name, e.employee_name, e.department, e.designation).where(e.status == "Active")
		)
		for col, val in (
			("department", self.department),
			("branch", self.branch),
			("designation", self.designation),
			("work_type", self.work_type),
			("grade", self.grade),
		):
			if val:
				q = q.where(getattr(e, col) == val)
		for f in advanced_filters:
			if len(f) < 3:
				continue
			fieldname = f[0]
			operator = f[1]
			value = f[2]
			field = getattr(e, fieldname, None)
			if not field:
				continue
			if operator == "=":
				q = q.where(field == value)
			elif operator == "!=":
				q = q.where(field != value)
			elif operator == "in":
				q = q.where(field.isin(value))
			elif operator == "not in":
				q = q.where(field.notin(value))
			elif operator == "like":
				q = q.where(field.like(value))
			elif operator == ">":
				q = q.where(field > value)
			elif operator == "<":
				q = q.where(field < value)
			elif operator == ">=":
				q = q.where(field >= value)
			elif operator == "<=":
				q = q.where(field <= value)
		emps = q.run(as_dict=True)
		self.set("employees", [])
		for emp in emps:
			self.append(
				"employees",
				{
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"department": emp.department,
					"designation": emp.designation,
				},
			)
		return True

	def validate(self):
		self.validate_period_in_dates()
		self.set_status()

	def on_submit(self):
		employee_count = len(self.employees)
		if employee_count <= 25:
			self.db_set("status", "Processing")
			errors = self.create_employee_shift_management()
			if errors:
				self.db_set("error_log", "\n\n".join(errors))
				self.db_set("status", "Failed")
			else:
				self.db_set("status", "Completed")
		else:
			self.db_set("status", "Queued")
			enqueue(
				create_esmb_background,
				docname=self.name,
				queue="long",
				timeout=6000,
				enqueue_after_commit=True
			)
			msgprint(
				_("Processing queued for {0} employees. This may take a few minutes.").format(employee_count),
				alert=True,
				indicator="blue"
			)

	def set_status(self, status=None, update=False):
		if not status:
			if self.docstatus == 0:
				status = "Draft"
			elif self.docstatus == 2:
				status = "Cancelled"
			else:
				return
		if update:
			self.db_set("status", status)
		else:
			self.status = status

	def validate_period_in_dates(self):
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		shift_dates = set()
		for s in self.shifts_period:
			shift_date = getdate(s.shift_date)
			if not (start_date <= shift_date <= end_date):
				frappe.throw(
                    f"Row {s.idx}: Shift Date {shift_date} not in period between {start_date} and {end_date}"
                )
			if shift_date in shift_dates:
				frappe.throw(
                    f"Duplicate shift date found in Row {s.idx}: {shift_date}"
                )
			shift_dates.add(shift_date)
		current = start_date
		while current <= end_date:
			if current not in shift_dates:
				frappe.throw(
                    f"Missing shift on {current.strftime('%Y-%m-%d')}. All dates must be covered without gaps."
                )
			current += timedelta(days=1)

	def create_employee_shift_management(self):
		"""Creates ESM draft records per employee. Returns list of error strings for failures."""
		errors = []
		for e in self.employees:
			try:
				args = {
					'employee': e.employee,
					'employee_name': e.employee_name,
					'department': e.department,
					'posting_date': self.posting_date,
					'start_date': self.start_date,
					'end_date': self.end_date,
					'bulk_ref': self.name,
					'saturday_st': self.saturday_st,
					'sunday_st': self.sunday_st,
					'monday_st': self.monday_st,
					'tuesday_st': self.tuesday_st,
					'wednesday_st': self.wednesday_st,
					'thursday_st': self.thursday_st,
					'friday_st': self.friday_st,
					'shifts_period': self.shifts_period
				}
				frappe.new_doc('Employee Shift Management').update(args).insert()
			except Exception as ex:
				errors.append(f"Employee {e.employee} ({e.employee_name}): {str(ex)}")
		return errors

	@frappe.whitelist()
	def submit_all_employees(self):
		drafts = frappe.get_all(
			"Employee Shift Management",
			filters={"bulk_ref": self.name, "docstatus": 0},
			fields=["name"]
		)
		if not drafts:
			msgprint(_("No pending Employee Shift Management records to submit."), alert=True, indicator="orange")
			return
		if len(drafts) <= 25:
			errors = _submit_esm_list(drafts)
			self.db_set("employees_submitted", 1)
			if errors:
				existing_log = self.error_log or ""
				separator = "\n\n--- Submit Errors ---\n" if existing_log else ""
				self.db_set("error_log", existing_log + separator + "\n\n".join(errors))
				msgprint(
					_("Submitted {0} record(s) with {1} failure(s). See Error Log for details.").format(
						len(drafts) - len(errors), len(errors)
					),
					alert=True,
					indicator="orange"
				)
			else:
				msgprint(
					_("Submitted {0} Employee Shift Management record(s).").format(len(drafts)),
					alert=True,
					indicator="green"
				)
		else:
			enqueue(
				submit_all_employees_background,
				docname=self.name,
				queue="long",
				timeout=6000,
				enqueue_after_commit=True
			)
			msgprint(
				_("Submitting {0} Employee Shift Management records in the background. This may take a few minutes.").format(len(drafts)),
				alert=True,
				indicator="blue"
			)


def _submit_esm_list(drafts):
	"""Submit ESM records one by one. Returns list of error strings for any failures."""
	errors = []
	for row in drafts:
		try:
			doc = frappe.get_doc("Employee Shift Management", row.name)
			doc.submit()
		except Exception as ex:
			employee = frappe.db.get_value("Employee Shift Management", row.name, "employee") or row.name
			errors.append(f"ESM {row.name} (Employee {employee}): {str(ex)}")
	return errors


def submit_all_employees_background(docname):
	try:
		drafts = frappe.get_all(
			"Employee Shift Management",
			filters={"bulk_ref": docname, "docstatus": 0},
			fields=["name"]
		)
		errors = _submit_esm_list(drafts)
		frappe.db.set_value("Employee Shift Management Bulk", docname, "employees_submitted", 1)
		if errors:
			existing_log = frappe.db.get_value("Employee Shift Management Bulk", docname, "error_log") or ""
			separator = "\n\n--- Submit Errors ---\n" if existing_log else ""
			frappe.db.set_value(
				"Employee Shift Management Bulk", docname,
				"error_log", existing_log + separator + "\n\n".join(errors)
			)
	except Exception:
		traceback = frappe.get_traceback()
		frappe.log_error(traceback, f"Submit All Employees failed for {docname}")


def create_esmb_background(docname):
	try:
		doc = frappe.get_doc("Employee Shift Management Bulk", docname)
		if doc.docstatus != 1:
			doc.db_set("status", "Cancelled")
			return
		doc.db_set("status", "Processing")
		errors = doc.create_employee_shift_management()
		if errors:
			frappe.db.set_value(
				"Employee Shift Management Bulk", docname,
				"error_log", "\n\n".join(errors)
			)
			frappe.db.set_value(
				"Employee Shift Management Bulk", docname,
				"status", "Failed"
			)
		else:
			frappe.db.set_value(
				"Employee Shift Management Bulk", docname,
				"status", "Completed"
			)
	except Exception:
		traceback = frappe.get_traceback()
		frappe.log_error(traceback, f"Bulk Shift Management failed for {docname}")
		frappe.db.set_value("Employee Shift Management Bulk", docname, "status", "Failed")
		frappe.db.set_value("Employee Shift Management Bulk", docname, "error_log", traceback)
