# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt
import frappe
import datetime
from datetime import datetime

from frappe.model.document import Document
class EmployeeShiftManagement(Document):
    pass

##### from mahmoud 
@frappe.whitelist()
def check_active_status(employee):
    sql = frappe.db.sql ("""
        SELECT name
        FROM `tabEmployee Shift Management` tesm 
        WHERE docstatus = 1 AND status = 'Active'
        AND employee = %s
    """ , (employee))
    if sql: 
        return 1 
    return 0 



@frappe.whitelist()
def create_shift_assignment(name):
    result = frappe.db.sql ("""
        SELECT employee ,posting_date , start_date , end_date , saturday_shift_type , sunday_shift_type ,
            monday_shift_type , tuesday_shift_type , wednesday_shift_type , thursday_shift_type , 
            friday_shift_type
            FROM `tabEmployee Shift Management` tesm 
            WHERE name = %s
        """ , (name) , as_dict =True)
    employee = result[0]['employee']
    start_date = result[0]['start_date']
    end_date = result[0]['end_date']
    posting_date = (result[0]['posting_date']).weekday()
    today = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][posting_date]
    active_day = today.lower()+"_shift_type"
    active_shift = result[0][active_day]
    shift_type = list()
    shift_type.append(str(result[0]['saturday_shift_type']))
    shift_type.append(str(result[0]['sunday_shift_type']))
    shift_type.append(str(result[0]['monday_shift_type']))
    shift_type.append(str(result[0]['tuesday_shift_type']))
    shift_type.append(str(result[0]['wednesday_shift_type']))
    shift_type.append(str(result[0]['thursday_shift_type']))
    shift_type.append(str(result[0]['friday_shift_type']))
    shift_type = list(set(shift_type))
    for i in shift_type:
        if 'None' in shift_type:
            shift_type.remove('None')
    shift_management = frappe.db.sql("""
    SELECT name  
    FROM `tabShift Assignment` tsa 
    WHERE employee = %s  AND status = 'Active' 
    """ , (employee), as_dict = True)
    if shift_management:
        for status in shift_management:
            shift_management_name = status.get('name')
            frappe.db.set_value('Shift Assignment' , shift_management_name , 'status', 'Inactive')
            doc = frappe.get_doc('Shift Assignment', shift_management_name)
            doc.save()

    for type in shift_type:
        shift = frappe.new_doc('Shift Assignment')
        shift.employee = employee
        shift.start_date = start_date
        shift.end_date = end_date
        shift.shift_type = type
        shift.custom_employee_shift_management = name
        if type == active_shift:
            shift.status = 'Active'
        else :
            shift.status = 'Inactive'
        shift.insert(ignore_permissions = True)
        shift.save()
        shift.submit()
    return f"Shift Assignments created for {employee} with types: {shift_type}"
