# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_weekday, add_days, formatdate
from frappe import db, enqueue, msgprint, _
from datetime import timedelta

class EmployeeShiftManagement(Document):
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
        

    def validate(self): 
        self.validate_period_in_dates()
        self.set_status()
        
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
            exists = frappe.db.exists(
                "Shift Assignment",
                {
                    "employee": self.employee,
                    "start_date": shift_date,
                    "end_date": shift_date,
                    "docstatus": ("<", 2)
                }
            )
            if exists:
                frappe.throw(f"Employee {self.employee} have Active Shift Assignment for Date {shift_date}")     
        current = start_date
        while current <= end_date:
            if current not in shift_dates:
                frappe.throw(
                    f"Missing shift on {current.strftime('%Y-%m-%d')}. All dates must be covered without gaps."
                )
            current += timedelta(days=1)
            
    def on_submit(self): 
        self.create_shift_assigment_enqueue()
        self.set_status(update=True, status="Submitted")
        
    def on_cancel(self):
        self.set_status(update=True, status="Cancelled")  
        
    def create_shift_assigment_enqueue(self): 
        self.db_set("status", "Queued")
        enqueue(
            create_shift_assignments_for_doc,
            docname=self.name,
            queue="long",
            timeout=3000,
            enqueue_after_commit=True
        )
        msgprint(
            _("Shift Assignment creation is queued. It may take a few minutes"),
            alert=True,
            indicator="blue",
        )
        
    def set_status(self, status=None, update=False):
        if not status:
            status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus or 0]
        if update:
            self.db_set("status", status)
        else:
            self.status = status

def create_shift_assignments_for_doc(docname):
    try:
        doc = frappe.get_doc("Employee Shift Management", docname)
        if doc.docstatus != 1:
            doc.db_set("status", "Cancelled")
            return
        for s in doc.shifts_period: 
            shift_date = s.shift_date     
            exists = frappe.db.exists(
                "Shift Assignment",
                {
                    "employee": doc.employee,
                    "start_date": shift_date,
                    "end_date": shift_date,
                    "docstatus": ("<", 2)
                }
            )
            if exists:
                continue 
            assignment = frappe.get_doc({
                "doctype": "Shift Assignment",
                "employee": doc.employee,
                "shift_type": s.shift_type,
                "start_date": shift_date,
                "end_date": shift_date, 
                "custom_employee_shift_management": doc.name
            })
            assignment.insert()
            assignment.submit()
        db.set_value(
            "Employee Shift Management", 
            docname, 
            "status", 
            "Submitted"
        )
        
    except Exception as e:
        frappe.log_error(f"Shift Assignment creation failed for {docname}")
        db.set_value(
            "Employee Shift Management", 
            docname, 
            "status", 
            "Failed"
        )
