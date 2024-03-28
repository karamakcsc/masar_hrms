# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt


# import frappe
import frappe
# from __future__ import unicode_literals
import erpnext, json
from frappe import _, scrub, ValidationError
from frappe.utils import flt, comma_or, nowdate, getdate
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe.model.document import Document
from frappe.model.document import Document
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from frappe.model.document import Document

class EmployeeOvertime(Document):
    def __init__(self, *args, **kwargs):
        super(EmployeeOvertime, self).__init__(*args, **kwargs)

    def on_submit(self):
        #  pass
        self.defAddAdditionalSalary()



    def defAddAdditionalSalary(self,submit=True):
        employee = self.employee
        salary_component = self.salary_component
        payroll_date = self.posting_date
        hour_rate_wd= flt(self.basic_salary) / 240 * self.overtime_rate_working_hour
        hour_rate_od= flt(self.basic_salary) / 240 * self.overtime_rate_off_day
        deduct_amount = flt(self.overtime_hours_working_day * hour_rate_wd)	+ flt(self.overtime_hours_off_day * hour_rate_od)
        entry = {
            "employee": employee,
            "salary_component": salary_component,
            "company": self.company,
            "currency": frappe.get_doc("Company", self.company).default_currency,
            "amount": flt(deduct_amount),
            "payroll_date": payroll_date,
            'deduct_full_tax_on_selected_payroll_date': 1 
        }
        frappe.new_doc("Additional Salary").update(entry).insert(ignore_permissions=True, ignore_mandatory=True).run_method('submit')

        frappe.db.commit()


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


@frappe.whitelist()
def get_employee_attendance(date_from, date_to, department=None):
    get_draft_overtime(date_from, date_to, department)
    ################# subimt the overtime here after execute the function 
    exist_employee = frappe.db.sql(f"""
            SELECT name 
            FROM `tabEmployee Overtime` teo 
            WHERE  posting_date = '{date_to}'
        """, as_dict=True)
    for emp in exist_employee:
        overtime_doc =frappe.get_doc("Employee Overtime" , emp['name'] )
        overtime_doc.save()
        overtime_doc.submit()
        frappe.db.commit()        
    # frappe.msgprint(str(exist_employee))
    return 'done'

    

def get_draft_overtime(date_from, date_to, department=None):
    cond = ""
    if department:
        cond += f" AND te.department = '{department}'"
    attendance_list = frappe.db.sql(f"""
      WITH AttSh AS (
            SELECT
                tas.employee,
                tas.employee_name,
                tas.attendance_date,
               (IFNULL(tas.difference_hours, 0)) AS shortage_hours
            FROM `tabAttendance Shortage` tas
            WHERE tas.is_overtime = 1 
            AND tas.attendance_date BETWEEN '{date_from}' AND '{date_to}'
        ),
        ATTSH_OFD AS (
            SELECT
                tas.employee,
                tas.employee_name,
                (IFNULL(tas.difference_hours, 0)) AS shortage_hours_wofd
            FROM `tabAttendance Shortage` tas
            WHERE tas.working_off_day = 1 
            AND tas.attendance_date BETWEEN '{date_from}' AND '{date_to}'
        ),
        LeaveSH AS (
            SELECT
                tsla.employee,
                tsla.employee_name,
                (IFNULL(tsla.total_leave_hours, 0)) AS leave_hours
            FROM `tabShort Leave Application` tsla
            WHERE tsla.posting_date BETWEEN '{date_from}' AND '{date_to}'
            GROUP BY employee
        )
        SELECT
            a.employee,
            a.employee_name,
            a.attendance_date , 
            IFNULL(a.shortage_hours, 0) AS shortage_hours,
            IFNULL(o.shortage_hours_wofd, 0) AS shortage_hours_wofd,
            IFNULL(l.leave_hours, 0) AS leave_hours,
            IFNULL(a.shortage_hours, 0) - IFNULL(l.leave_hours, 0) AS not_covered_hours,
            te.overtime_ceiling 
        FROM AttSh a
        LEFT JOIN LeaveSH l ON a.employee = l.employee
        LEFT JOIN ATTSH_OFD o ON a.employee = o.employee
        INNER JOIN tabEmployee te ON a.employee = te.name AND te.is_overtime_applicable = 1 AND te.status = 'Active' {cond} 
        ORDER BY a.attendance_date ASC
 
    """, as_dict=True)

    for attendance in attendance_list:
        result = get_salary_structure_assignment(attendance.employee)
        exist_employee = frappe.db.sql(f"""
            SELECT employee, posting_date 
            FROM `tabEmployee Overtime` teo 
            WHERE employee = '{attendance.get('employee')}' AND posting_date = '{date_to}'
        """, as_dict=True)
        if exist_employee:
            data_emp = frappe.db.sql(f"""
            SELECT teo.name ,teo.overtime_rate_working_hour , teo.overtime_rate_off_day , 
            teo.overtime_hours_working_day , teo.basic_salary , teo.overtime_hours_off_day , 
            teo.unallocated_off_day , teo.unallocated_wd
            FROM `tabEmployee Overtime` teo 
            WHERE teo.employee = '{exist_employee[0]['employee']}'  AND teo.posting_date =  '{date_to}'
            """ , as_dict = True)
            if data_emp:
                exist_data = data_emp[0]
                if exist_data['unallocated_off_day']:
                    unallocated_off_day_old = float(exist_data['unallocated_off_day'])
                else:
                    unallocated_off_day_old = 0.0
                if exist_data['unallocated_wd']:
                    unallocated_wd_old= float(exist_data['unallocated_wd']) 
                else:
                    unallocated_wd_old = 0.0
                ### Hours already in Empoloyee overtime working day
                if exist_data['overtime_hours_working_day']:
                    overtime_wd_old = float(exist_data['overtime_hours_working_day'])
                else:
                    overtime_wd_old= 0 
                ### Hours already in Empoloyee overtime Off day
                if exist_data['overtime_hours_off_day']:
                    overtime_off_old = float(exist_data['overtime_hours_off_day'])
                else:
                    overtime_off_old = 0 
                #### get new overtime hours for Employee
                overtime_wd_new = float(attendance.get('shortage_hours'))
                overtime_off_new = float(attendance.get('shortage_hours_wofd'))
                out = 0.0 
                in_off_hours = 0.0
                in_wd_hours = 0.0
                unallocated_off_day_new = 0.0 
                unallocated_wd_new = 0.0 
                all_hours = overtime_wd_old + overtime_off_old + overtime_wd_new + overtime_off_new
                overtime_ceiling = float(attendance.get('overtime_ceiling')) 

                #### if all hous less than cieling ( Add all hours to employee)
                if all_hours < overtime_ceiling:
                    entry = {
                    "overtime_hours_working_day":(float(overtime_wd_old) + float(overtime_wd_new)),
                    "overtime_hours_off_day": (float(overtime_off_old) + float(overtime_off_new)),
                    }
                    overtime_doc =( frappe.get_doc("Employee Overtime" ,exist_data.name ).update(entry).save())
                    calculate_overtime_employee(attendance.employee, overtime_doc, date_to)

                #### if  add working day new  , it less tha ciling but if add off day new  make the total hours bigger than ceiling 
                elif float(all_hours) > float(overtime_ceiling) and float(overtime_wd_old + overtime_off_old + overtime_wd_new)< float(overtime_ceiling):
                    out = all_hours - overtime_ceiling
                    in_off_hours = overtime_off_new - out
                    unallocated_off_day_new =  (float(unallocated_off_day_old) + float(out)) 
                    # frappe.msgprint(f"{in_off_hours}")
                    entry = {
                    "overtime_hours_working_day":(float(overtime_wd_old) + float(overtime_wd_new)),
                    "overtime_hours_off_day": (float(overtime_off_old) + float(in_off_hours)),
                    'unallocated_off_day' : unallocated_off_day_new
                    }
                    overtime_doc =( frappe.get_doc("Employee Overtime" ,exist_data.name ).update(entry).save())
                    calculate_overtime_employee(attendance.employee, overtime_doc, date_to)


                #### if add working day new make the total hours bigger than ceiling 
                elif (overtime_wd_old +overtime_off_old) < overtime_ceiling and (overtime_wd_old +overtime_off_old + overtime_wd_new) > overtime_ceiling:
                    out = (overtime_wd_old +overtime_off_old + overtime_wd_new) - overtime_ceiling
                    in_wd_hours = overtime_wd_new - out
                    unallocated_wd_new = (float(unallocated_wd_old) + float(out)) 
                    unallocated_off_day_new =  float(overtime_off_new) + float(unallocated_off_day_old)
                    # frappe.msgprint(f"33333333")
                    entry = {
                    "overtime_hours_working_day":(float(overtime_wd_old) + float(in_wd_hours)),
                    'unallocated_wd' :unallocated_wd_new ,
                    'unallocated_off_day': unallocated_off_day_new
                    }
                    overtime_doc =( frappe.get_doc("Employee Overtime" ,exist_data.name ).update(entry).save())
                    calculate_overtime_employee(attendance.employee, overtime_doc, date_to)


                elif (overtime_wd_old + overtime_off_old) >= overtime_ceiling:
                    unallocated_wd_new = float(unallocated_wd_old )+ float(overtime_wd_new)
                    unallocated_off_day_new = float(overtime_off_new) + float(unallocated_off_day_old)
                    # frappe.msgprint(f"employee : {attendance.employee} ,,,,,,,,,,,,,,, 4")
                    entry = {
                    "unallocated_wd":unallocated_wd_new,
                    "unallocated_off_day": unallocated_off_day_new,
                    }
                    overtime_doc =( frappe.get_doc("Employee Overtime" ,exist_data.name ).update(entry).save())
                    calculate_overtime_employee(attendance.employee, overtime_doc, date_to) 
        else:
            entry = {
                "employee": attendance.get('employee'),
                "overtime_hours_working_day": attendance.get('shortage_hours'),
                "overtime_hours_off_day": attendance.get('shortage_hours_wofd'),
                "not_covered_hours": attendance.get('not_covered_hours'),
                "salary_structure_assignment": result,
                "posting_date": date_to
            }
            overtime_doc = frappe.new_doc("Employee Overtime").update(entry).insert(ignore_permissions=True, ignore_mandatory=True)
            # overtime_doc.save
            calculate_overtime_employee(attendance.employee, overtime_doc, date_to)

def calculate_overtime_employee(employee, overtime_doc , date_to):
    data = frappe.db.sql("""
            SELECT teo.name ,teo.overtime_rate_working_hour , teo.overtime_rate_off_day , 
            teo.overtime_hours_working_day , teo.basic_salary , teo.overtime_hours_off_day
            FROM `tabEmployee Overtime` teo 
            WHERE teo.employee =%s AND posting_date = %s
        """ , (employee , date_to), as_dict = True)
    basic_salary =float(data[0]['basic_salary'])
    overtime_rate_working_hour = float(data[0]['overtime_rate_working_hour'])
    overtime_rate_off_day = float(data[0]['overtime_rate_off_day'])
    overtime_hours_working_day = float(data[0]['overtime_hours_working_day'])  
    overtime_hours_off_day =  float(data[0]['overtime_hours_off_day'])
    rate_hours_working_day = ( basic_salary /240) * overtime_rate_working_hour
    rate_hours_off_day  = (basic_salary /240 ) * overtime_rate_off_day
    amount_working_day = rate_hours_working_day * overtime_hours_working_day
    amount_off_day = rate_hours_off_day * overtime_hours_off_day
    total_amount = amount_working_day + amount_off_day
    entry = {
        "rate_hours_working_day":rate_hours_working_day,
        "rate_hours_off_day": rate_hours_off_day,
        "amount_working_day": amount_working_day,
        "overtime_hours_off_day": overtime_hours_off_day,
        "amount_off_day": amount_off_day,
        "total_amount": total_amount
    }
    overtime_doc.update(entry)
    overtime_doc.save()
    # overtime_doc.submit()
    frappe.db.commit()