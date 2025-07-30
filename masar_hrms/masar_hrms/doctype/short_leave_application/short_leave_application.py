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
            return to_time_obj.time().strftime("%H:%M:%S")
        return None
    @frappe.whitelist()
    def get_leave_salary_and_hour_rate(self):
        hr_settings_doc = frappe.get_doc('HR Settings')
        standard_working_hours = float(hr_settings_doc.standard_working_hours)
        if standard_working_hours in [0 , None]:
            standard_working_hours = 8
        if self.employee:
            salary = 0 
            employee_doc = frappe.get_doc('Employee', self.employee)
            for r in employee_doc.custom_salary_component_table:
                if r.is_active == 1: 
                    salary += float(r.esc_amount)
            return {
                'hourly_rate': salary / 30 / standard_working_hours if salary else 0,
                'leave_salary': salary
            }
        else:
            return {'hourly_rate': 0, 'salary': 0}
    @frappe.whitelist()    
    def get_total_amount_by_duration(self):
        if self.leave_duration and self.leave_duration > 0:
            leave_salary_and_hour_rate = self.get_leave_salary_and_hour_rate()
            hourly_rate = leave_salary_and_hour_rate['hourly_rate']
            total_amount = (self.leave_duration / 3600) * hourly_rate
            return total_amount
        else:
            frappe.throw(_("Leave duration must be greater than zero."), title=_("Invalid Leave Duration"))
    def validate(self):
        self.leave_approver_setting_validation()
        self.general_required_fields_validation()
        if (self.balance_deduction + self.salary_deduction+ self.none_deduction) != 1:
                frappe.throw(
                    """Please select only one of the following options: Balance Deduction, Salary Deduction, or None Deduction.""",
                    title=_("Deduction Type Required")
                )
        if self.balance_deduction:
            self.get_leave_balance()
            self.check_leave_time_in_shift()
        if self.salary_deduction:
            self.check_if_casual_balance_is_available()
    def on_submit(self):
        self.status_validation()
        if self.status == 'Approved':
            if (self.balance_deduction + self.salary_deduction+ self.none_deduction) != 1:
                frappe.throw(
                    """Please select only one of the following options: Balance Deduction, Salary Deduction, or None Deduction.""",
                    title=_("Deduction Type Required")
                )
            if self.balance_deduction:
                self.leave_balance_submittion()
            
    def leave_approver_setting_validation(self):
        hr_setting = frappe.get_doc('HR Settings')
        leave_approver_mandatory_in_leave_application = hr_setting.leave_approver_mandatory_in_leave_application
        if leave_approver_mandatory_in_leave_application and self.leave_approver is None : 
            frappe.throw(
				"""No leave approver has been assigned for this Employee : {employee}.<br> 
				Please assign a Leave Approver Before Proceeding.""".format(employee=self.employee),
				title=_("Leave Approver Required")
			)
    def general_required_fields_validation(self):
        if not self.leave_date:
            frappe.throw(_("Leave Date is required for this Short Leave Application."), title=_("Leave Date Required"))
        if not self.from_time:
            frappe.throw(_("From Time is required for this Short Leave Application."), title=_("From Time Required"))
        if not self.leave_duration or float(self.leave_duration) <= 0:
            frappe.throw(_("Leave Duration must be greater than zero."), title=_("Invalid Leave Duration"))
            
    def status_validation(self):
        if self.status not in ['Approved' , 'Rejected']:
            frappe.throw('''Only Leave Applications with status 'Approved' and 'Rejected' can be submitted''')        
    
    def leave_balance_submittion(self):
        if self.leave_duration and self.leave_duration > 14400:
            self.full_day_leave_application()
        else:
            self.calculate_leave_application()

    def full_day_leave_application(self):
        self.create_leave_application()
        
        
    def get_standard_working_hours_in_seconds(self):
        hr_settings_doc = frappe.get_doc('HR Settings')
        standard_working_hours = float(hr_settings_doc.standard_working_hours)
        if standard_working_hours in [0 , None]:
            standard_working_hours = 8
        hours = int(standard_working_hours)
        minutes = int((standard_working_hours - hours) * 60)
        swh_in_seconds = hours * 3600 + minutes * 60
        return swh_in_seconds


    def calculate_leave_application(self):
        swh_in_seconds = self.get_standard_working_hours_in_seconds()
        if not swh_in_seconds:
            frappe.throw("""Standard Working Hours have not been defined in the HR Settings. <br>
                            Please enter the required working hours to proceed.""" , title=_("Standard Working Hours")
            )
        total_leaves = self.get_leaves_totals()
        sla_in_seconds = total_leaves['sla_in_seconds']
        leave_in_seconds = total_leaves['leave_in_seconds']
        if float(self.leave_duration) <= 0 :
            frappe.throw(
                "Leave duration cannot be zero. Please enter a valid leave duration." , 
                title=_("Missing Leave Duration")
            )
        if (sla_in_seconds - leave_in_seconds ) >= swh_in_seconds:
            self.create_leave_application()
            
    def create_leave_application(self):
            new_leave_app_doc = frappe.new_doc('Leave Application')
            new_leave_app_doc.employee = self.employee
            new_leave_app_doc.employee_name = self.employee_name
            new_leave_app_doc.leave_type = self.leave_type
            new_leave_app_doc.company = self.company
            new_leave_app_doc.department = self.department
            new_leave_app_doc.from_date = self.leave_date
            new_leave_app_doc.to_date = self.leave_date
            new_leave_app_doc.total_leave_days = 1 
            new_leave_app_doc.leave_approver = self.leave_approver if self.leave_approver else None
            new_leave_app_doc.posting_date = self.leave_date
            new_leave_app_doc.custom_esla_ref = self.name
            new_leave_app_doc.status ="Approved"
            new_leave_app_doc.insert(ignore_permissions=True)
            new_leave_app_doc.submit()
            frappe.msgprint(
                "The Leave Application has been Successfully Created and Submitted.",
                alert=True,
                indicator='green'
            )            
    def get_leaves_totals(self):
        sla = frappe.qb.DocType('Short Leave Application')
        la = frappe.qb.DocType('Leave Application')
        sql = (frappe.qb.from_(sla)
            .join(la)
            .on(sla.name == la.custom_esla_ref)
            .select(
                (Sum(sla.leave_duration)).as_('sla_amount'),
                (Sum(la.total_leave_days)).as_('leave_days')
            )
            .where(sla.docstatus == 1)
            .where(sla.status == 'Approved')
            .where(sla.balance_deduction == 1)
            .where(sla.leave_type == self.leave_type)
            .where(sla.employee == self.employee)
            .where(sla.leave_duration <= 14400)
        ).run(as_dict = True)
        if sql and sql[0]:
            return {
                'sla_in_seconds': sql[0]['sla_amount'] if sql[0]['sla_amount'] else 0 ,
                'leave_in_seconds': self.convert_leaves_day_to_second(sql[0]['leave_days'] if sql[0]['leave_days'] else 0 )  
            }
        else:
            return {
                'sla_in_seconds': 0 ,
                'leave_in_seconds': 0     
            }
    def convert_leaves_day_to_second(self , leave_days):
        seconds_in_day = self.get_standard_working_hours_in_seconds()
        return leave_days * seconds_in_day
    
    def check_leave_time_in_shift(self):
        shift_assignment = self.get_shift_assiggnment_active()
        if not shift_assignment:
            frappe.throw(_("No active shift assignment found for the employee on the selected date."))
        shift_type = frappe.get_doc('Shift Type', shift_assignment['shift_type'])
        from_time = datetime.strptime(str(self.from_time), "%H:%M:%S").time()
        to_time =  datetime.strptime(str(self.get_to_time()), "%H:%M:%S").time()
        shift_start = datetime.strptime(str(shift_type.start_time), "%H:%M:%S").time()
        shift_end = datetime.strptime(str(shift_type.end_time), "%H:%M:%S").time()
        if from_time < shift_start or to_time > shift_end:
            frappe.throw(
                _("Leave time must be within the shift hours: {start} to {end}.").format(
                    start=shift_type.start_time, end=shift_type.end_time
                ),
                title=_("Invalid Leave Time")
            )
        
        
    def check_if_casual_balance_is_available(self):
        if not self.employee:
            frappe.throw(_("Employee is required to check casual balance."), title=_("Employee Required"))
        leave_balance = get_leave_balance_on(self.employee, 'Casual Vacation', self.leave_date)
        if leave_balance or leave_balance > 1:
            frappe.throw(
                """Casual Vacation balance is available for the employee on the selected date.
                Please select Balance Deduction or None Deduction.""",
                title=_("Casual Vacation Balance Available")
            )
    
