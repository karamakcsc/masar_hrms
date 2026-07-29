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
            has_conflict = frappe.db.sql("""
                SELECT name FROM `tabShift Assignment`
                WHERE employee = %s
                AND docstatus < 2
                AND start_date <= %s
                AND (end_date >= %s OR end_date IS NULL)
                LIMIT 1
            """, (self.employee, shift_date, shift_date))
            if has_conflict:
                frappe.throw(
                    f"Employee {self.employee} has an active Shift Assignment covering {shift_date}"
                )
        current = start_date
        while current <= end_date:
            if current not in shift_dates:
                frappe.throw(
                    f"Missing shift on {current.strftime('%Y-%m-%d')}. All dates must be covered without gaps."
                )
            current += timedelta(days=1)

    @frappe.whitelist()
    def submit_to_bulk_processing(self):
        company = frappe.db.get_value("Employee", self.employee, "company")
        bulk = frappe.new_doc("Employee Shift Management Bulk")
        bulk.company = company
        bulk.posting_date = self.posting_date
        bulk.start_date = self.start_date
        bulk.end_date = self.end_date
        bulk.saturday_st = self.saturday_st
        bulk.sunday_st = self.sunday_st
        bulk.monday_st = self.monday_st
        bulk.tuesday_st = self.tuesday_st
        bulk.wednesday_st = self.wednesday_st
        bulk.thursday_st = self.thursday_st
        bulk.friday_st = self.friday_st
        bulk.append("employees", {
            "employee": self.employee,
            "employee_name": self.employee_name,
            "department": self.department
        })
        for s in self.shifts_period:
            bulk.append("shifts_period", {
                "shift_date": s.shift_date,
                "shift_day": s.shift_day,
                "shift_type": s.shift_type,
                "start_time": s.start_time,
                "end_time": s.end_time
            })
        bulk.insert()
        bulk.submit()
        return bulk.name

    def on_submit(self):
        periods_count = len(self.shifts_period)
        if periods_count <= 100:
            self.create_shift_assignments_inline()
        else:
            self._enqueue_shift_assignments()

    def on_cancel(self):
        self.set_status(update=True, status="Cancelled")

    def create_shift_assignments_inline(self):
        groups = _group_shift_periods(self.shifts_period)
        frappe.db.savepoint("esm_shift_assignments")
        try:
            for shift_type, start_date, end_date in groups:
                has_overlap = frappe.db.sql("""
                    SELECT name FROM `tabShift Assignment`
                    WHERE employee = %s
                    AND docstatus < 2
                    AND start_date <= %s
                    AND (end_date >= %s OR end_date IS NULL)
                    LIMIT 1
                """, (self.employee, end_date, start_date))
                if has_overlap:
                    frappe.db.rollback_to_savepoint("esm_shift_assignments")
                    frappe.throw(
                        f"Shift Assignment conflict for {self.employee} in period {start_date} to {end_date}"
                    )
                assignment = frappe.get_doc({
                    "doctype": "Shift Assignment",
                    "employee": self.employee,
                    "shift_type": shift_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "custom_employee_shift_management": self.name
                })
                assignment.insert()
                assignment.submit()
            self.db_set("status", "Completed")
        except frappe.ValidationError:
            frappe.db.rollback_to_savepoint("esm_shift_assignments")
            raise
        except Exception as e:
            frappe.db.rollback_to_savepoint("esm_shift_assignments")
            frappe.throw(str(e))

    def _enqueue_shift_assignments(self):
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


def _group_shift_periods(periods):
    sorted_periods = sorted(periods, key=lambda s: getdate(s.shift_date))
    if not sorted_periods:
        return []
    groups = []
    current_shift = sorted_periods[0].shift_type
    current_start = getdate(sorted_periods[0].shift_date)
    current_end = getdate(sorted_periods[0].shift_date)
    for s in sorted_periods[1:]:
        shift_date = getdate(s.shift_date)
        if s.shift_type == current_shift:
            current_end = shift_date
        else:
            groups.append((current_shift, current_start, current_end))
            current_shift = s.shift_type
            current_start = shift_date
            current_end = shift_date
    groups.append((current_shift, current_start, current_end))
    return groups


def create_shift_assignments_for_doc(docname):
    doc = None
    try:
        doc = frappe.get_doc("Employee Shift Management", docname)
        if doc.docstatus != 1:
            doc.db_set("status", "Cancelled")
            return
        doc.db_set("status", "Processing")
        groups = _group_shift_periods(doc.shifts_period)
        frappe.db.savepoint("esm_bg_shift_assignments")
        for shift_type, start_date, end_date in groups:
            has_overlap = frappe.db.sql("""
                SELECT name FROM `tabShift Assignment`
                WHERE employee = %s
                AND docstatus < 2
                AND start_date <= %s
                AND (end_date >= %s OR end_date IS NULL)
                LIMIT 1
            """, (doc.employee, end_date, start_date))
            if has_overlap:
                continue
            assignment = frappe.get_doc({
                "doctype": "Shift Assignment",
                "employee": doc.employee,
                "shift_type": shift_type,
                "start_date": start_date,
                "end_date": end_date,
                "custom_employee_shift_management": doc.name
            })
            assignment.insert()
            assignment.submit()
        db.set_value("Employee Shift Management", docname, "status", "Completed")
    except Exception as e:
        if doc:
            frappe.db.rollback_to_savepoint("esm_bg_shift_assignments")
        traceback = frappe.get_traceback()
        frappe.log_error(traceback, f"Shift Assignment creation failed for {docname}")
        db.set_value("Employee Shift Management", docname, "status", "Failed")
        db.set_value("Employee Shift Management", docname, "error_reason", str(e)[:140])
        db.set_value("Employee Shift Management", docname, "error_log", traceback)
