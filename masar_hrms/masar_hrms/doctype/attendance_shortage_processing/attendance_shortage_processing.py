# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

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

# class AttendanceShortageProcessing(Document):
# 	pass

class AttendanceShortageProcessing(Document):
#     def __init__(self, *args, **kwargs):
#         super(AttendanceShortageProcessing, self).__init__(*args, **kwargs)
#     def on_submit(self):
#         self.AddAdditionalSalary()

#     # def validate(self):
#         # self.AddAdditionalSalary()
  
#     def AddAdditionalSalary(self, submit=True):
#         employee = self.employee
#         salary_component = self.salary_component
#         payroll_date = self.date_to
#         working_hours = calculate_working_hours(employee,payroll_date)

#         hour_rate = flt(self.basic_salary) / 240
#         deduct_amount = flt(self.shortage_hours * hour_rate * 1)
#         entry = {
#             "employee": employee,
#             "salary_component": self.salary_component,
#             "company": self.company,
#             "currency": frappe.get_doc("Company", self.company).default_currency,
#             "amount": flt(deduct_amount),
#             "payroll_date": self.date_to,

#         }
#         (frappe.new_doc("Additional Salary")
#             .update(entry)
#             .insert(ignore_permissions=True, ignore_mandatory=True)).run_method('submit')
#         frappe.db.commit()



# @frappe.whitelist()
# def calculate_working_hours(employee, posting_date):
#     posting_date = datetime.strptime(posting_date, "%Y-%m-%d")
#     result = get_employee_shift(employee, posting_date)
#     working_hours = 0

#     if result:
#         if result.start_datetime.minute > result.end_datetime.minute:
#             working_hours = datetime.time(
#                 result.end_datetime.hour - result.start_datetime.hour - 1,
#                 60 - result.start_datetime.minute + result.end_datetime.minute
#             )
#         else:
#             working_hours = datetime.time(
#                 result.end_datetime.hour - result.start_datetime.hour,
#                 result.end_datetime.minute - result.start_datetime.minute
#             )
#     elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
#         working_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
#     else:
#         working_hours = 0

#     return working_hours



# # @frappe.whitelist()
# # def get_employee_attendance(date_from, date_to):
# #     attendance_list = frappe.db.sql("""
# #         WITH AttSh AS (
# #             SELECT
# #                 tas.employee,
# #                 tas.employee_name,
# #                 SUM(IFNULL(tas.difference_hours, 0)) AS shortage_hours
# #             FROM `tabAttendance Shortage` tas
# #             WHERE tas.is_shortage = 1 AND tas.attendance_date BETWEEN %s AND %s
# #             GROUP BY employee
# #         ),
# #         LeaveSH AS (
# #             SELECT
# #                 tsla.employee,
# #                 tsla.employee_name,
# #                 SUM(IFNULL(tsla.total_leave_hours, 0)) AS leave_hours
# #             FROM `tabShort Leave Application` tsla
# #             WHERE tsla.posting_date BETWEEN %s AND %s
# #             GROUP BY employee
# #         )
# #         SELECT
# #             a.employee,
# #             a.employee_name,
# #             IFNULL(shortage_hours, 0) AS shortage_hours,
# #             IFNULL(leave_hours, 0) AS leave_hours,
# #             IFNULL(shortage_hours, 0) - IFNULL(leave_hours, 0) AS not_covered_hours
# #         FROM AttSh a
# #         LEFT JOIN LeaveSh l ON a.employee = l.employee
# #     """, (date_from, date_to, date_from, date_to), as_dict=True)

# #     for attendance in attendance_list:
# #         entry = {
# #             "employee": attendance.employee,
# #             "date_from": date_from,
# #             "date_to": date_to,
# #             "shortage_hours": attendance.shortage_hours,
# #             "leave_hours": attendance.leave_hours,
# #             "not_covered_hours": attendance.not_covered_hours,
# #         }
# #         (frappe.new_doc("Attendance Shortage Processing")
# #             .update(entry)
# #             .insert(ignore_permissions=True, ignore_mandatory=True)
# #             .run_method('save'))
# #         frappe.db.commit()



# # @frappe.whitelist()
# # def get_salary_structure_assignment(employee=None):
# #     result = frappe.get_list(
# #         "Salary Structure Assignment",
# #         filters={'employee': employee, 'docstatus': 1},
# #         fields=['name'],
# #         order_by='creation DESC',
# #         limit=1
# #     )

# #     if result:
# #         return result[0].name
# #     else:
# #         return 0
# #     doc.save()




# @frappe.whitelist()
# def get_employee_attendance(date_from, date_to):
#     attendance_list = frappe.db.sql("""
#         WITH AttSh AS (
#             SELECT
#                 tas.employee,
#                 tas.employee_name,
#                 SUM(IFNULL(tas.difference_hours, 0)) AS shortage_hours
#             FROM `tabAttendance Shortage` tas
#             WHERE tas.is_shortage = 1 AND tas.attendance_date BETWEEN %s AND %s
#             GROUP BY employee
#         ),
#         LeaveSH AS (
#             SELECT
#                 tsla.employee,
#                 tsla.employee_name,
#                 SUM(IFNULL(tsla.total_leave_hours, 0)) AS leave_hours
#             FROM `tabShort Leave Application` tsla
#             WHERE tsla.posting_date BETWEEN %s AND %s
#             GROUP BY employee
#         )
#         SELECT
#             a.employee,
#             a.employee_name,
#             IFNULL(shortage_hours, 0) AS shortage_hours,
#             IFNULL(leave_hours, 0) AS leave_hours,
#             IFNULL(shortage_hours, 0) - IFNULL(leave_hours, 0) AS not_covered_hours
#         FROM AttSh a
#         LEFT JOIN LeaveSh l ON a.employee = l.employee
#     """, (date_from, date_to, date_from, date_to), as_dict=True)

#     for attendance in attendance_list:
#         result = get_salary_structure_assignment(attendance.employee)
#         entry = {
#             "employee": attendance.employee,
#             "date_from": date_from,
#             "date_to": date_to,
#             "shortage_hours": attendance.shortage_hours,
#             "leave_hours": attendance.leave_hours,
#             "not_covered_hours": attendance.not_covered_hours,
#             "salary_structure_assignment": result
#         }
#         (frappe.new_doc("Attendance Shortage Processing")
#             .update(entry)
#             .insert(ignore_permissions=True, ignore_mandatory=True)
#             .run_method('submit'))
#         frappe.db.commit()


# @frappe.whitelist()
# def get_salary_structure_assignment(employee=None):
#     result = frappe.get_list(
#         "Salary Structure Assignment",
#         filters={'employee': employee, 'docstatus': 1},
#         fields=['name'],
#         order_by='creation DESC',
#         limit=1
#     )

#     if result:
#         return result[0].name
#     else:
#         return 0





##################################################################################################################################
   
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
################################################################################################################################## 
##################################################################################################################################
    def __init__(self, *args, **kwargs):
        super(AttendanceShortageProcessing, self).__init__(*args, **kwargs)
    def on_submit(self):
        self.AddAdditionalSalary()

    # def validate(self):
        # self.AddAdditionalSalary()
  
    def AddAdditionalSalary(self, submit=True):
        employee = self.employee
        salary_component = self.salary_component
        payroll_date = self.date_to
        working_hours = calculate_working_hours(employee,payroll_date)
        hour_rate = flt(self.basic_salary) / 240
        # deduct_amount = flt(self.shortage_hours * hour_rate * 1)
        ### edit deduct amount from mahmoud 
        differences_leave_duration = self.differences_leave_duration / 3600 
        deduct_amount = flt(differences_leave_duration * hour_rate * 1)
        entry = {
            "employee": employee,
            "salary_component": self.salary_component,
            "company": self.company,
            "currency": frappe.get_doc("Company", self.company).default_currency,
            "amount": flt(deduct_amount),
            "payroll_date": self.date_to,

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
def get_employee_attendance(date_from, date_to):
    attendance_list = frappe.db.sql("""
        WITH AttSh AS (
            SELECT
                tas.employee,
                tas.employee_name,
                SUM(IFNULL(tas.difference_hours, 0)) AS shortage_hours
            FROM `tabAttendance Shortage` tas
            WHERE tas.is_shortage = 1 AND tas.attendance_date BETWEEN %s AND %s
            GROUP BY employee
        ),
        LeaveSH AS (
            SELECT
                tsla.employee,
                tsla.employee_name,
                SUM(IFNULL(tsla.total_leave_hours, 0)) AS leave_hours
            FROM `tabShort Leave Application` tsla
            WHERE tsla.posting_date BETWEEN %s AND %s
            GROUP BY employee
        )
        SELECT
            a.employee,
            a.employee_name,
            IFNULL(shortage_hours, 0) AS shortage_hours,
            IFNULL(leave_hours, 0) AS leave_hours,
            IFNULL(shortage_hours, 0) - IFNULL(leave_hours, 0) AS not_covered_hours
        FROM AttSh a
        LEFT JOIN LeaveSh l ON a.employee = l.employee
    """, (date_from, date_to, date_from, date_to), as_dict=True)
    for attendance in attendance_list:
        result = get_salary_structure_assignment(attendance.employee)
        ############## mahmoud child table start code
        child_table_data_sql = frappe.db.sql("""
            SELECT name, leave_duration , posting_date
            FROM `tabShort Leave Application` tsla 
            WHERE employee = %s AND posting_date BETWEEN %s AND %s
        """, (attendance['employee'], date_from, date_to), as_dict=True)
        child_entries = []
        total_leave_duration = list()
        for child_table_data in child_table_data_sql:
            child_entries.append({
                'short_leave_application': child_table_data.get('name'),
                'leave_duration': child_table_data.get('leave_duration'), 
                'posting_date' : child_table_data.get('posting_date'), 
                'remark': 1,
            })
            total_leave_duration.append(child_table_data.get('leave_duration'))
            frappe.db.set_value('Short Leave Application' , child_table_data.get('name') , 'attendance_shortage_processing_reference' , )
        differences_leave_duration = max(0, (attendance.shortage_hours * 3600) - sum(total_leave_duration))

        ############## mahmoud child table end code 
        entry = {
            "employee": attendance.employee,
            "date_from": date_from,
            "date_to": date_to,
            "shortage_hours": attendance.shortage_hours,
            "leave_hours": attendance.leave_hours,
            "not_covered_hours": attendance.not_covered_hours,
            "salary_structure_assignment": result ,  
            ### the lines below from mahoud 
            "short_leave_application": child_entries ,
            "total_leave_duration" : sum(total_leave_duration) , 
            "differences_leave_duration": differences_leave_duration, 
            ######## End from mahmoud 
        }
        new_doc = (frappe.new_doc("Attendance Shortage Processing")
            .update(entry)
            .insert(ignore_permissions=True, ignore_mandatory=True)
            .run_method('submit'))
        frappe.db.commit()
        ###### From mahmoud to add attendance shortage processing reference to attendance shortage processing
        for child_table_data in child_table_data_sql:
            frappe.db.set_value('Short Leave Application' , child_table_data.get('name') , 'attendance_shortage_processing_reference' , new_doc.name)
        ###### end from mahmoud 

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
