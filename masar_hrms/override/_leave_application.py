import frappe
from frappe.utils import getdate
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication as _LeaveApplication


class LeaveApplication(_LeaveApplication):
	def create_or_update_attendance(self, attendance_name, date):
		if self.custom_work_injury_ref:
			status = "Injured"
		elif self.half_day_date and getdate(date) == getdate(self.half_day_date):
			status = "Half Day"
		else:
			status = "On Leave"

		if attendance_name:
			doc = frappe.get_doc("Attendance", attendance_name)
			half_day_status = None if status == "On Leave" else "Present"
			modify_half_day_status = 1 if doc.status == "Absent" and status == "Half Day" else 0
			doc.db_set(
				{
					"status": status,
					"leave_type": self.leave_type,
					"leave_application": self.name,
					"half_day_status": half_day_status,
					"modify_half_day_status": modify_half_day_status,
				}
			)
		else:
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.employee_name = self.employee_name
			doc.attendance_date = date
			doc.company = self.company
			doc.leave_type = self.leave_type
			doc.leave_application = self.name
			doc.status = status
			doc.half_day_status = "Present" if status == "Half Day" else None
			doc.modify_half_day_status = 1 if status == "Half Day" else 0
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
			doc.submit()
