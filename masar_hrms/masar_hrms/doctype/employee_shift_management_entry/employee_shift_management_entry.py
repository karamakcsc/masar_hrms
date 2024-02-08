# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond

from frappe import _

class EmployeeShiftManagementEntry(Document):
	pass

@frappe.whitelist()
def fill_employee_details(doc, department=None):
    condition = ""
    values = []

    if department:
        condition = "WHERE department = %s"
        values.append(department)

    sql_query = f"""
        SELECT name , employee_name , department 
        FROM tabEmployee te 
        {condition}
    """

    sql_result = frappe.db.sql(sql_query, tuple(values), as_dict=True)
    return sql_result

@frappe.whitelist()
def create_esm(doc, posting_date, status, end_date, start_date, saturday_st=None, wednesday_st=None, sunday_st=None, thursday_st=None, monday_st=None, friday_st=None, tuesday_st=None):
    employee_sql = frappe.db.sql("""
        SELECT employee
            FROM `tabEmployee Shift Management Entry Detail` tesmed 
            WHERE parent = %s
        """, (doc), as_list=True)
    for employee in employee_sql:
        new_doc = frappe.new_doc('Employee Shift Management')
        new_doc.employee = employee[0]  
        new_doc.posting_date = posting_date
        new_doc.status = status
        new_doc.end_date = end_date
        new_doc.start_date = start_date
        new_doc.saturday_shift_type = saturday_st
        new_doc.sunday_shift_type = sunday_st
        new_doc.monday_shift_type = monday_st
        new_doc.tuesday_shift_type = tuesday_st
        new_doc.wednesday_shift_type = wednesday_st
        new_doc.thursday_shift_type = thursday_st
        new_doc.friday_shift_type = friday_st
        new_doc.save(ignore_permissions=True)
        new_doc.submit()

    