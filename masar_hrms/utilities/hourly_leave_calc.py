from __future__ import unicode_literals
import frappe, erpnext, hrms
from frappe.utils import flt, cstr, nowdate, comma_and
from frappe import throw, msgprint, _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
import datetime

def SetHourlyLeaveForEmployee(self,method):
        data = frappe.db.sql("""
                select l.employee_no, sum(l.duration) as total_duration from `tabHourly Leave Employee` as l
                left join `tabHourly Leave Type` as t on l.hourly_leave_type=t.hourly_leave_type
                where employee_no = %s
            	  and l.docstatus = 1
            	  and leave_date >= %s
            	  and leave_date <= %s
                  and effecting_type = 'Salary Deduction'
                  Group By l.employee_no
                  """,(self.employee,self.start_date,self.end_date) ,as_dict=True)

        for d in data:
            self.hourly_leaves = d.total_duration
