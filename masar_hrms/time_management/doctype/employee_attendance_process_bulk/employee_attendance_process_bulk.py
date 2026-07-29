# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import db, qb, get_doc, throw, bold, _
from datetime import timedelta, datetime
from masar_hrms.time_management.doctype.employee_attendance_process.employee_attendance_process import (
	EmployeeAttendanceProcess as EAP,
)


class EmployeeAttendanceProcessBulk(Document):

	def number_of_day(self):
		return 30

	def get_basic_salary_component(self):
		basic = db.get_value('Company', self.company, 'custom_basic_salary_component')
		if basic is None:
			throw("Set Basic Salary Component in Company")
		return basic

	@frappe.whitelist()
	def insert_employees(self, advanced_filters: list | None = None):
		if not advanced_filters:
			advanced_filters = []
		e = qb.DocType("Employee")
		q = (
			qb.from_(e).select(e.name,e.employee_name,e.department,e.designation,).where(e.status == "Active")
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

	@frappe.whitelist()
	def get_standard_date_period(self):
		if self.posting_date is None:
			return False
		if isinstance(self.posting_date, str):
			posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d').date()
		else:
			posting_date = self.posting_date
		start_month = posting_date.replace(day=1)
		next_month = start_month.replace(day=28) + timedelta(days=4)
		end_month = next_month - timedelta(days=next_month.day)
		return {'from_date': start_month, 'to_date': end_month}

	def validate(self):
		self.employee_validate()
		self.date_validate()

	def on_submit(self):
		self.create_employee_att_process()

	def employee_validate(self):
		for e in self.employees:
			basic_salary = self._get_basic_salary(e.employee)
			if basic_salary in [0, None]:
				throw(_(f"Employee {bold(e.employee)} must have an active Basic Salary component."))
			if not db.get_value('Employee', e.employee, 'is_overtime_applicable'):
				throw(_(f"Employee {bold(e.employee)} must be marked as overtime applicable."))

	def date_validate(self):
		if not (self.from_date <= self.posting_date <= self.to_date):
			throw(_(
				f"Posting Date must be within the period between "
				f"{bold(self.from_date)} and {bold(self.to_date)}."
			))
		for e in self.employees:
			overlapping = frappe.db.exists(
				'Employee Attendance Process',
				{
					"employee": e.employee,
					"docstatus": ["!=", 2],
					"from_date": ["<=", self.to_date],
					"to_date": [">=", self.from_date],
				}
			)
			if overlapping:
				throw(_(
					f"An overlapping record already exists for Employee {bold(e.employee)} "
					f"within the period {bold(self.from_date)} to {bold(self.to_date)}."
				))

	def _get_basic_salary(self, employee):
		est = qb.DocType('Employee Salary Table')
		result = (
			qb.from_(est)
			.where(est.parent == employee)
			.where(est.is_active == 1)
			.where(est.salary_component == self.get_basic_salary_component())
			.select(est.esc_amount)
		).run()
		return result[0][0] if result else 0

	def create_employee_att_process(self):
		"""Create draft EAP records for each employee. Skips employees with errors."""
		errors = []
		created = 0

		for e in self.employees:
			try:
				eap = frappe.new_doc('Employee Attendance Process')
				eap.company = self.company
				eap.employee = e.employee
				eap.employee_name = e.employee_name
				eap.department = e.department
				eap.posting_date = self.posting_date
				eap.from_date = self.from_date
				eap.to_date = self.to_date
				eap.eapb_ref = self.name

				salary = EAP.get_salary_details(eap)
				eap.basic_salary = salary.get('basic_salary')
				eap.basic_salary_hour_rate = salary.get('hour_rate')
				eap.shortage_hour_rate = salary.get('shortage_hour_rate')
				eap.earning_salary = salary.get('earning_salary')
				EAP.get_overtime_type_as_defualt(eap)

				eap.save()
				frappe.db.commit()
				created += 1
			except Exception as exc:
				frappe.db.rollback()
				errors.append(f"{e.employee} ({e.employee_name}): {exc}")

		if errors:
			frappe.log_error(
				title=f"EAPB {self.name} – partial failures",
				message="\n".join(errors)
			)
			frappe.msgprint(
				_(
					"{0} EAP records created. The following employees were skipped due to errors:<br>{1}"
				).format(created, "<br>".join(errors)),
				indicator="orange",
				title=_("Partial Success"),
			)
		else:
			frappe.msgprint(
				_(f"{created} Attendance Process records created successfully."),
				indicator="green",
			)

	@frappe.whitelist()
	def submit_all_processes(self):
		"""Submit all draft EAP records linked to this bulk document."""
		eap_list = frappe.get_all(
			'Employee Attendance Process',
			filters={'eapb_ref': self.name, 'docstatus': 0},
			fields=['name', 'employee', 'employee_name'],
		)

		if not eap_list:
			frappe.msgprint(_("No draft Attendance Process records found to submit."))
			return {'success': 0, 'failed': 0, 'errors': []}

		success = 0
		errors = []

		for eap in eap_list:
			try:
				doc = frappe.get_doc('Employee Attendance Process', eap.name)
				doc.submit()
				frappe.db.commit()
				success += 1
			except Exception as exc:
				frappe.db.rollback()
				errors.append(f"{eap.employee} ({eap.employee_name}): {exc}")

		if errors:
			frappe.log_error(
				title=f"EAPB {self.name} – submit failures",
				message="\n".join(errors)
			)
			frappe.msgprint(
				_(
					"{0} submitted, {1} failed.<br><br>Failures:<br>{2}"
				).format(success, len(errors), "<br>".join(errors)),
				indicator="orange",
				title=_("Submit Result"),
			)
		else:
			frappe.msgprint(
				_(f"All {success} records submitted successfully."),
				indicator="green",
				title=_("Success"),
			)

		return {'success': success, 'failed': len(errors), 'errors': errors}
