import frappe
import masar_hrms
# from masar_hrms import masar_hrms
import erpnext, json
from frappe import _, scrub, ValidationError
import datetime
import requests
import calendar
from datetime import datetime, timedelta
from frappe.utils import flt, comma_or, nowdate, getdate
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe.model.document import Document
from frappe.model.document import Document
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from frappe.model.document import Document
# import string
# import random

def all():
    pass

# def cron():
#     letters = string.ascii_letters
#     note = " ".join(random.choice(letters) for i in range(20))

#     new_note = frappe.get_doc({"doctype": "Note",
#                                "title": note
#                                })
#     new_note.insert()
#     frappe.db.commit()

def cron():
    # Assuming you have a list of attendance records
    attendance_list = frappe.get_list("Attendance", filters={"status": "Present"}, fields=["name", "employee", "attendance_date", "status","shift","working_hours", "late_entry", "early_exit", "out_time", "in_time"])

    # Loop through the attendance list
    for attendance in attendance_list:
        
        # Calculate the shift working hours
        if attendance.shift:
            shift_type = frappe.get_doc("Shift Type", attendance.shift) 
            plan_hours=0
            if shift_type:
                # Convert the time field to an integer
                start_time_object = datetime.strptime(str(shift_type.start_time), "%H:%M:%S")
                start_time_in_second = timedelta(hours=start_time_object.hour, minutes=start_time_object.minute, seconds=start_time_object.second).total_seconds()

                end_time_object = datetime.strptime(str(shift_type.end_time), "%H:%M:%S")
                end_time_in_seconds = timedelta(hours=end_time_object.hour, minutes=end_time_object.minute, seconds=end_time_object.second).total_seconds()
                plan_hours = (end_time_in_seconds - start_time_in_second) / 3600
            elif frappe.db.get_single_value("HR Settings", "standard_working_hours"):
                plan_hours=frappe.db.get_single_value("HR Settings", "standard_working_hours")                
 
            # Check if employee is not working full day
            attendance_name = attendance.name
            employee = attendance.employee
            status = attendance.status
            shift =  attendance.shift
            attendance_date = attendance.attendance_date  
            working_hours = attendance.working_hours
            late_entry = attendance.late_entry
            early_exit = attendance.early_exit
            in_time = attendance.in_time
            out_time = attendance.out_time
            difference_hours = (plan_hours - working_hours)
            if plan_hours > working_hours and working_hours != 0:
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
                                    "in_time" : in_time,
                                    "out_time": out_time,
                                    "plan_hours": plan_hours,
                                    "difference_hours": difference_hours

                                })
                new_note.insert(ignore_permissions=True, ignore_mandatory=True)
                frappe.db.commit()

def daily():
    current_date = datetime.now()
    today_name = current_date.weekday()
    today = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today_name]
    day_shift_type = today.lower()+'_shift_type' ### day #### make sure in lower case when use
    shift_assignment_sql = frappe.db.sql("""
    SELECT custom_employee_shift_management, name , shift_type
    FROM `tabShift Assignment` tsa
    WHERE docstatus =1 
    """, as_dict=True)
    custom_employee_shift_management_list = list(set(entry['custom_employee_shift_management'] for entry in shift_assignment_sql))
    for custom_employee_shift_management in custom_employee_shift_management_list:
        employee_shift_management = frappe.db.sql("""
        SELECT  saturday_shift_type , sunday_shift_type , monday_shift_type , tuesday_shift_type , wednesday_shift_type , 
                thursday_shift_type , friday_shift_type
                FROM `tabEmployee Shift Management` tesm 
                WHERE status = 'Active' AND docstatus = 1 AND name = %s
        """,(custom_employee_shift_management)  , as_dict=True)
        new_shift = employee_shift_management[0][day_shift_type]
        for shift_assignment in shift_assignment_sql:
            name = shift_assignment.get('name')
            old_shift_type = shift_assignment.get('shift_type')
            if new_shift == None:
                status = 'Inactive' 
            elif new_shift == old_shift_type:
                status = 'Active' 
            elif new_shift != old_shift_type:
                status = 'Inactive' 
            frappe.db.set_value('Shift Assignment' , name , 'status', status)
            doc = frappe.get_doc('Shift Assignment', name)
            doc.save()


## this Task for Attendance Shortage 
def monthly(): 
    date = datetime.now().date()
    first_day_of_month = date.replace(day=1)
    last_day_of_month = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    attendance_list = frappe.get_list("Attendance", filters={"status": "Present", "attendance_date": ["between", [first_day_of_month, last_day_of_month]]}, fields=["name", "employee", "attendance_date", "status", "shift", "working_hours", "late_entry", "early_exit", "out_time", "in_time", "company"])
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
        difference_hours =   working_hours  - plan_hours
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
                "difference_hours": -1 * difference_hours,
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
                "working_off_day": is_working_off_day,
                "holiday_list": holiday_list  
            })
        if new_note:
            new_note.insert(ignore_permissions=True, ignore_mandatory=True)
            frappe.db.commit()