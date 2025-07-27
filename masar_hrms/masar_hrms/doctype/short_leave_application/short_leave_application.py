# # Copyright (c) 2023, KCSC and contributors
# # For license information, please see license.txt

import frappe
from frappe import _ , throw
from datetime import datetime, timedelta
from frappe.query_builder.functions import  Sum
from frappe.model.document import Document
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
class ShortLeaveApplication(Document):
    @frappe.whitelist()
    def get_shift_assiggnment_active(self):
        if self.employee and self.leave_date:
            shift_assignment = frappe.get_all(
				'Shift Assignment',
				filters={
					'employee': self.employee,
					'start_date': ['<=', self.leave_date],
					'end_date': ['>=', self.leave_date],
     				'docstatus': 1	, 
          			'status': 'Active'
				},
				fields=['name' , 'shift_type']
			)
            if shift_assignment:
                return {
					'shift_type': shift_assignment[0].shift_type,
					'shift_assignment': shift_assignment[0].name
           		}
            else: 
                throw(_('No active shift assignment found for the employee on the selected date.'))
        else:
            return 0 
        
    @frappe.whitelist()
    def get_leave_balance(self):
        if self.employee and self.leave_type:
            leave_balance = get_leave_balance_on(self.employee, self.leave_type, self.leave_date)
            if leave_balance:
                return leave_balance
            else:
                throw(_('No leave balance found for the employee on the selected date.'))
        else:
            return 0
        
    @frappe.whitelist()
    def get_to_time(self):
        if self.from_time and self.leave_duration:
            from_time_obj = datetime.strptime(str(self.from_time), "%H:%M:%S")
            to_time_obj = from_time_obj + timedelta(seconds=self.leave_duration)
            print(to_time_obj.time().strftime("%H:%M:%S"))
            return to_time_obj.time().strftime("%H:%M:%S")