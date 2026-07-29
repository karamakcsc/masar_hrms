# Copyright (c) 2025, KCSC and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from erpnext.setup.doctype.employee.test_employee import make_employee

from masar_hrms.injury.doctype.work_injury_settings.work_injury_settings import get_settings

TEST_EMPLOYEE_EMAIL = "test_work_injury_crossmonth@example.com"
TEST_BASIC_COMPONENT = "_Test WI Basic"
TEST_DEDUCTION_COMPONENT = "_Test WI Injury Deduction"
TEST_PROJECT_NAME = "_Test WI Project"


class TestWorkInjury(FrappeTestCase):
	# Work Injury Settings is a Single doctype (one row for the whole site) and Leave Type's
	# custom_is_injury flag must be unique site-wide (get_leave_type() throws otherwise), so both
	# are snapshotted here and restored in tearDown instead of relying on rollback semantics.
	def setUp(self):
		self.company = frappe.get_all("Company", limit=1, pluck="name")[0]
		self.employee = make_employee(TEST_EMPLOYEE_EMAIL, company=self.company)

		self._settings_snapshot = get_settings().as_dict()
		self._created_leave_type = False

		self.leave_type = self._ensure_injury_leave_type()
		self.project = self._ensure_project()
		self._ensure_salary_components()
		self._configure_work_injury_settings()

	def tearDown(self):
		# Restore via a direct DB write (not settings.save()) since the pre-test snapshot
		# may have blank values for fields that are mandatory-on-save (e.g. on a site where
		# Work Injury Settings was never configured through the UI before this test ran).
		for fieldname in (
			"employee_paid_days",
			"ss_percent_ded",
			"leave_type",
			"wage_calculation_base",
			"basic_salary_component",
			"injury_deduction_component",
			"require_medical_approval",
			"cost_limit",
		):
			frappe.db.set_single_value(
				"Work Injury Settings", fieldname, self._settings_snapshot.get(fieldname)
			)
		frappe.clear_cache(doctype="Work Injury Settings")

		if self._created_leave_type:
			frappe.delete_doc("Leave Type", self.leave_type, force=True, ignore_permissions=True)

	def _ensure_injury_leave_type(self):
		existing = frappe.get_all("Leave Type", filters={"custom_is_injury": 1}, limit=1, pluck="name")
		if existing:
			return existing[0]

		self._created_leave_type = True
		return frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test WI Injury Leave",
				"custom_is_injury": 1,
			}
		).insert(ignore_permissions=True).name

	def _ensure_project(self):
		existing = frappe.db.exists("Project", {"project_name": TEST_PROJECT_NAME, "company": self.company})
		if existing:
			return existing

		return frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": TEST_PROJECT_NAME,
				"company": self.company,
			}
		).insert(ignore_permissions=True).name

	def _ensure_salary_components(self):
		if not frappe.db.exists("Salary Component", TEST_BASIC_COMPONENT):
			frappe.get_doc(
				{
					"doctype": "Salary Component",
					"salary_component": TEST_BASIC_COMPONENT,
					"salary_component_abbr": "TWIB",
					"type": "Earning",
					"depends_on_payment_days": 0,
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists("Salary Component", TEST_DEDUCTION_COMPONENT):
			frappe.get_doc(
				{
					"doctype": "Salary Component",
					"salary_component": TEST_DEDUCTION_COMPONENT,
					"salary_component_abbr": "TWID",
					"type": "Deduction",
					"depends_on_payment_days": 0,
				}
			).insert(ignore_permissions=True)

	def _configure_work_injury_settings(self):
		settings = get_settings()
		settings.employee_paid_days = 3
		settings.ss_percent_ded = 25
		settings.leave_type = self.leave_type
		settings.wage_calculation_base = "Basic Salary"
		settings.basic_salary_component = TEST_BASIC_COMPONENT
		settings.injury_deduction_component = TEST_DEDUCTION_COMPONENT
		settings.require_medical_approval = 0
		settings.cost_limit = 0
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="Work Injury Settings")

	def _make_slip_stub(self, start_date, end_date, total_working_days, basic_amount):
		"""A lightweight, unsaved Salary Slip used to exercise the injury deduction
		math directly, without pulling in a full Salary Structure/payroll run."""
		slip = frappe.new_doc("Salary Slip")
		slip.employee = self.employee
		slip.start_date = start_date
		slip.end_date = end_date
		slip.total_working_days = total_working_days
		slip.append(
			"earnings",
			{
				"salary_component": TEST_BASIC_COMPONENT,
				"amount": basic_amount,
				"default_amount": basic_amount,
				"depends_on_payment_days": 0,
			},
		)
		return slip

	def test_cross_month_injury_deduction(self):
		"""A Work Injury spanning 28 Jan - 9 Feb (4 + 9 = 13 days), with Employee Paid
		Days = 3, must only grant the 3 free days once, on the case's first payroll
		period - the second period's deduction must start immediately on day 1."""
		work_injury = frappe.get_doc(
			{
				"doctype": "Work Injury",
				"employee": self.employee,
				"company": self.company,
				"injury_no": "TEST-WI-CROSSMONTH",
				"injury_location": self.project,
				"injury_start_date": "2026-01-28",
				"injuries": [{"no_of_days": 4}],  # 28, 29, 30, 31 Jan
			}
		)
		work_injury.insert(ignore_permissions=True)
		work_injury.set_end_date()
		work_injury.submit()

		work_injury.reload()
		self.assertEqual(work_injury.total_days, 4)
		self.assertEqual(work_injury.employer_paid_days, 3)
		self.assertEqual(work_injury.deduction_days, 1)

		january_injured_days = frappe.get_all(
			"Attendance",
			filters={
				"employee": self.employee,
				"status": "Injured",
				"docstatus": 1,
				"attendance_date": ["between", ["2026-01-28", "2026-01-31"]],
			},
		)
		self.assertEqual(len(january_injured_days), 4)

		# Doctor extension after submit: 9 more days (1-9 Feb), exercising allow_on_submit.
		work_injury.append("injuries", {"no_of_days": 9})
		work_injury.set_end_date()
		work_injury.save(ignore_permissions=True)

		work_injury.reload()
		self.assertEqual(work_injury.total_days, 13)
		self.assertEqual(work_injury.employer_paid_days, 3)
		self.assertEqual(work_injury.deduction_days, 10)

		february_injured_days = frappe.get_all(
			"Attendance",
			filters={
				"employee": self.employee,
				"status": "Injured",
				"docstatus": 1,
				"attendance_date": ["between", ["2026-02-01", "2026-02-09"]],
			},
		)
		self.assertEqual(len(february_injured_days), 9)

		settings = get_settings()

		# January: 4 injured days, 3 of which are still inside the case's fully-paid
		# window -> only 1 deductible day. daily_rate = 3100 / 31 = 100.
		january_slip = self._make_slip_stub("2026-01-01", "2026-01-31", 31, 3100)
		january_deduction = january_slip.get_work_injury_deduction_amount(settings)
		self.assertEqual(flt(january_deduction, 2), 25.0)  # 1 day * 100 * 25%

		january_slip.apply_work_injury_deduction()
		january_deduction_row = next(
			(r for r in january_slip.deductions if r.salary_component == TEST_DEDUCTION_COMPONENT), None
		)
		self.assertIsNotNone(january_deduction_row)
		self.assertEqual(flt(january_deduction_row.amount, 2), 25.0)

		# February: the case's fully-paid window (3 days) was already used up in
		# January, so all 9 February injured days are deductible from day 1.
		# daily_rate = 2800 / 28 = 100.
		february_slip = self._make_slip_stub("2026-02-01", "2026-02-28", 28, 2800)
		february_deduction = february_slip.get_work_injury_deduction_amount(settings)
		self.assertEqual(flt(february_deduction, 2), 225.0)  # 9 days * 100 * 25%

		february_slip.apply_work_injury_deduction()
		february_deduction_row = next(
			(r for r in february_slip.deductions if r.salary_component == TEST_DEDUCTION_COMPONENT), None
		)
		self.assertIsNotNone(february_deduction_row)
		self.assertEqual(flt(february_deduction_row.amount, 2), 225.0)
