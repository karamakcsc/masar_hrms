# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
import frappe, erpnext, json,datetime
import time
from datetime import date, datetime, time, timedelta
from frappe import _, scrub, ValidationError
from frappe.utils import cint, get_datetime, get_time, getdate
from frappe.model.document import Document
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from frappe.utils import flt, comma_or, nowdate, getdate
from hrms.hr.utils import (
    get_holiday_dates_for_employee,
    share_doc_with_approver,
)

from typing import Dict

from frappe.utils import (
    cint,
    get_fullname,
)

from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange

from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

class AttendanceShortage(Document):
    pass


class AttendanceShortage(Document):
    def __init__(self, *args, **kwargs):
        super(AttendanceShortage, self).__init__(*args, **kwargs)

    def validate(self):
        pass


    def on_update(self):

        if self.status == "Open" and self.docstatus < 1:
            # notify leave approver about creation
            if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
                self.notify_leave_approver()

        share_doc_with_approver(self, self.leave_approver)

    def on_submit(self):
        if self.action_type == "Deduct From Salary":
            # from_time = get_time(self.from_time)
                    attendance_date = datetime.strptime("20-03-2023", "%d-%m-%Y").date()
                    posting_date = datetime.combine(attendance_date, datetime.min.time())
                    result=get_employee_shift(self.employee, posting_date)

                    working_hours=0
                    if result:
                        if result.start_datetime.minute>result.end_datetime.minute:
                            working_hours=datetime.time(result.end_datetime.hour-result.start_datetime.hour-1,60-result.start_datetime.minute+result.end_datetime.minute)
                        else:
                            working_hours=datetime.time(result.end_datetime.hour-result.start_datetime.hour,result.end_datetime.minute-result.start_datetime.minute)
                    elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
                        working_hours=frappe.db.get_single_value("HR Settings", "standard_working_hours")
                    else: frappe.throw("You have to assign a shift for the employee or assign standar working hours in HR Settings")

                    if self.salary_component is None:
                        frappe.throw(_("Please Insert The Salary Componanet For This Employee"))

                    if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
                        self.notify_employee()

                        self.create_leave_ledger_entry(str(working_hours))
                    else:
                        if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
                            self.notify_employee()

                    self.AddAdditionalSalary()

    def AddAdditionalSalary(self, submit=True):
        employee = self.employee
        salary_component = self.salary_component
        payroll_date = self.attendance_date
        working_hours = calculate_working_hours(employee,payroll_date)

        hour_rate = flt(self.basic_salary) / 240
        deduct_amount = self.difference_hours * hour_rate
        entry = {
            "employee": employee,
            "salary_component": salary_component,
            "company": self.company,
            "currency": frappe.get_doc("Company", self.company).default_currency,
            "amount": flt(deduct_amount),
            "payroll_date": payroll_date,

        }
        (frappe.new_doc("Additional Salary")
            .update(entry)
            .insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
        frappe.db.commit()





@frappe.whitelist()
def calculate_working_hours(employee, posting_date):
    posting_date = datetime.strptime(posting_date, "%Y-%m-%d")
    result = get_employee_shift(employee, posting_date)
    working_hours = 0

    if result:
        if result.start_datetime.minute > result.end_datetime.minute:
            working_hours = datetime.time(
                result.end_datetime.hour - result.start_datetime.hour - 1,
                60 - result.start_datetime.minute + result.end_datetime.minute
            )
        else:
            working_hours = datetime.time(
                result.end_datetime.hour - result.start_datetime.hour,
                result.end_datetime.minute - result.start_datetime.minute
            )
    elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
        working_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
    else:
        working_hours = 0

    return working_hours



@frappe.whitelist()
def get_salary_structure_assignment(employee=None):
    result = frappe.get_list(
        "Salary Structure Assignment",
        filters={'employee': employee, 'docstatus': 1},
        fields=['name'],
        order_by='creation DESC',
        limit=1
    )

    if result:
        return result[0].name
    else:
        return 0
    doc.save()

# @frappe.whitelist()
# def get_employee_attendance(date_from, date_to):
#     # Assuming you have a list of attendance records
#     attendance_list = frappe.get_list("Attendance", filters={"status": "Present", "attendance_date": ["between", [date_from, date_to]]}, fields=["name", "employee", "attendance_date", "status", "shift", "working_hours", "late_entry", "early_exit", "out_time", "in_time"])

#     # Loop through the attendance list
#     for attendance in attendance_list:

#         # Calculate the shift working hours
#         if attendance.shift:
#             shift_type = frappe.get_doc("Shift Type", attendance.shift)
#             plan_hours=0
#             if shift_type:
#                 # Convert the time field to an integer
#                 start_time_object = datetime.strptime(str(shift_type.start_time), "%H:%M:%S")
#                 start_time_in_second = timedelta(hours=start_time_object.hour, minutes=start_time_object.minute, seconds=start_time_object.second).total_seconds()

#                 end_time_object = datetime.strptime(str(shift_type.end_time), "%H:%M:%S")
#                 end_time_in_seconds = timedelta(hours=end_time_object.hour, minutes=end_time_object.minute, seconds=end_time_object.second).total_seconds()
#                 plan_hours = (end_time_in_seconds - start_time_in_second) / 3600
#             elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
#                 plan_hours=frappe.db.get_single_value("HR Settings", "standard_working_hours")

#             # Check if employee is not working full day
#             attendance_name = attendance.name
#             employee = attendance.employee
#             status = attendance.status
#             shift =  attendance.shift
#             attendance_date = attendance.attendance_date
#             working_hours = attendance.working_hours
#             late_entry = attendance.late_entry
#             early_exit = attendance.early_exit
#             in_time = attendance.in_time
#             out_time = attendance.out_time
#             difference_hours = (plan_hours - working_hours)
#             if plan_hours > working_hours and working_hours != 0:
#                 new_note = frappe.get_doc({
#                                     "doctype": "Attendance Shortage",
#                                     "employee": employee,
#                                     "shift": shift,
#                                     "attendance_date": attendance_date,
#                                     "working_hours": working_hours,
#                                     "late_entry": late_entry,
#                                     "early_exit": early_exit,
#                                     "attendance": attendance_name,
#                                     "status": status,
#                                     "in_time" : in_time,
#                                     "out_time": out_time,
#                                     "plan_hours": plan_hours,
#                                     "difference_hours": difference_hours

#                                 })
#                 new_note.insert(ignore_permissions=True, ignore_mandatory=True)
#                 frappe.db.commit()

#################################################################################################
# @frappe.whitelist()
# def get_employee_attendance(date_from, date_to):
#     # Assuming you have a list of attendance records
#     attendance_list = frappe.get_list("Attendance", filters={"status": "Present", "attendance_date": ["between", [date_from, date_to]]}, fields=["name", "employee", "attendance_date", "status", "shift", "working_hours", "late_entry", "early_exit", "out_time", "in_time"])

#     for attendance in attendance_list:
#         # Check if the record already exists for the same employee and attendance date
#         existing_record = frappe.get_all("Attendance Shortage", filters={"employee": attendance.employee, "attendance_date": attendance.attendance_date})
#         if existing_record:
#             continue  # Skip the iteration if a record already exists

#         # Calculate the shift working hours
#         shift_type = frappe.get_doc("Shift Type", attendance.shift) if attendance.shift else None
#         if shift_type:
#             start_time_object = datetime.strptime(str(shift_type.start_time), "%H:%M:%S")
#             start_time_in_seconds = timedelta(hours=start_time_object.hour, minutes=start_time_object.minute, seconds=start_time_object.second).total_seconds()

#             end_time_object = datetime.strptime(str(shift_type.end_time), "%H:%M:%S")
#             end_time_in_seconds = timedelta(hours=end_time_object.hour, minutes=end_time_object.minute, seconds=end_time_object.second).total_seconds()

#             plan_hours = (end_time_in_seconds - start_time_in_seconds) / 3600
#         else:
#             plan_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")

#         # Assign the values to variables
#         employee = attendance.employee
#         shift = attendance.shift
#         attendance_date = attendance.attendance_date
#         working_hours = attendance.working_hours
#         late_entry = attendance.late_entry
#         early_exit = attendance.early_exit
#         in_time = attendance.in_time
#         out_time = attendance.out_time
#         attendance_name = attendance.name
#         status = attendance.status
#         difference_hours = working_hours - plan_hours

#         if working_hours > plan_hours:
#             # Insert the new record for overtime
#             new_note = frappe.get_doc({
#                 "doctype": "Attendance Shortage",
#                 "employee": employee,
#                 "shift": shift,
#                 "attendance_date": attendance_date,
#                 "working_hours": working_hours,
#                 "late_entry": late_entry,
#                 "early_exit": early_exit,
#                 "attendance": attendance_name,
#                 "status": status,
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "plan_hours": plan_hours,
#                 "difference_hours": difference_hours,
#                 "is_overtime": 1
#             })
#         elif working_hours < plan_hours:
#             # Insert the new record for shortage
#             new_note = frappe.get_doc({
#                 "doctype": "Attendance Shortage",
#                 "employee": employee,
#                 "shift": shift,
#                 "attendance_date": attendance_date,
#                 "working_hours": working_hours,
#                 "late_entry": late_entry,
#                 "early_exit": early_exit,
#                 "attendance": attendance_name,
#                 "status": status,
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "plan_hours": plan_hours,
#                 "difference_hours": difference_hours,
#                 "is_shortage": 1
#             })

#         new_note.insert(ignore_permissions=True, ignore_mandatory=True)
#         frappe.db.commit()
###################################################################################
@frappe.whitelist()
def get_employee_attendance(date_from, date_to):

    attendance_list = frappe.get_list("Attendance", filters={"status": "Present", "attendance_date": ["between", [date_from, date_to]]}, fields=["name", "employee", "attendance_date", "status", "shift", "working_hours", "late_entry", "early_exit", "out_time", "in_time", "company"])

    for attendance in attendance_list:
      
        existing_record = frappe.get_all("Attendance Shortage", filters={"employee": attendance.employee, "attendance_date": attendance.attendance_date})
        if existing_record:
            continue  

        shift_type = frappe.get_doc("Shift Type", attendance.shift) if attendance.shift else None
        if shift_type:
            start_time_object = datetime.strptime(str(shift_type.start_time), "%H:%M:%S")
            start_time_in_seconds = timedelta(hours=start_time_object.hour, minutes=start_time_object.minute, seconds=start_time_object.second).total_seconds()

            end_time_object = datetime.strptime(str(shift_type.end_time), "%H:%M:%S")
            end_time_in_seconds = timedelta(hours=end_time_object.hour, minutes=end_time_object.minute, seconds=end_time_object.second).total_seconds()

            plan_hours = (end_time_in_seconds - start_time_in_seconds) / 3600
            holiday_list = shift_type.holiday_list
        else:
            plan_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
            holiday_list = None

        if not holiday_list:
            company = frappe.get_doc("Company", attendance.company)
            holiday_list = company.default_holiday_list

        if not holiday_list:
            frappe.throw("Holiday List not found")

        try:
            holidays_doc = frappe.get_doc("Holiday List", holiday_list)
            holidays = holidays_doc.holidays
        except frappe.DoesNotExist:
            frappe.throw("Holidays not found in the Holiday List")

        is_working_off_day = 0
        for holiday in holidays:
            if holiday.holiday_date == attendance.attendance_date and holiday.weekly_off == 1:
                is_working_off_day = 1
                break
        employee = attendance.employee
        shift = attendance.shift
        attendance_date = attendance.attendance_date
        working_hours = attendance.working_hours
        late_entry = attendance.late_entry
        early_exit = attendance.early_exit
        in_time = attendance.in_time
        out_time = attendance.out_time
        attendance_name = attendance.name
        status = attendance.status
        difference_hours = plan_hours - working_hours

        new_note = None
        if working_hours > plan_hours:
            new_note = frappe.get_doc({
                "doctype": "Attendance Shortage",
                "employee": employee,
                "shift": shift,
                "attendance_date": attendance_date,
                "working_hours": working_hours,
                "late_entry": late_entry,
                "early_exit": early_exit,
                "attendance": attendance_name,
                "status": status,
                "in_time": in_time,
                "out_time": out_time,
                "plan_hours": plan_hours,
                "difference_hours": difference_hours,
                "is_overtime": 1,
                # "working_off_day": is_working_off_day,
                "holiday_list": holiday_list 
            })
        elif working_hours < plan_hours:  
            new_note = frappe.get_doc({
                "doctype": "Attendance Shortage",
                "employee": employee,
                "shift": shift,
                "attendance_date": attendance_date,
                "working_hours": working_hours,
                "late_entry": late_entry,
                "early_exit": early_exit,
                "attendance": attendance_name,
                "status": status,
                "in_time": in_time,
                "out_time": out_time,
                "plan_hours": plan_hours,
                "difference_hours": difference_hours,
                "is_shortage": 1,
                "working_off_day": is_working_off_day, 
                "holiday_list": holiday_list 
            })
        elif working_hours > plan_hours and is_working_off_day ==1 :
            new_note = frappe.get_doc({
                "doctype": "Attendance Shortage",
                "employee": employee,
                "shift": shift,
                "attendance_date": attendance_date,
                "working_hours": working_hours,
                "late_entry": late_entry,
                "early_exit": early_exit,
                "attendance": attendance_name,
                "status": status,
                "in_time": in_time,
                "out_time": out_time,
                "plan_hours": plan_hours,
                "difference_hours": difference_hours,
                # "is_overtime": 1,
                "working_off_day": is_working_off_day,
                "holiday_list": holiday_list  
            })

        if new_note:
            new_note.insert(ignore_permissions=True, ignore_mandatory=True)
            frappe.db.commit()