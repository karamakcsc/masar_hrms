# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AR3Print(Document):
    def validate(self):
        self.validate_date()
    
    
    def validate_date(self):
        if self.from_date and self.to_date and self.to_date < self.from_date:
            frappe.throw("The 'To Date' cannot be earlier than the 'From Date'.")
    
    @frappe.whitelist()
    def get_ss(self):    
        conditions = " tss.docstatus = 1 "
        if self.from_date and self.to_date:
            conditions += f" AND tss.end_date BETWEEN '{self.from_date}' AND '{self.to_date}'"
        if self.department:
            conditions += f" AND tss.department = '{self.department}'"
        ss_sql = frappe.db.sql(f"""
                SELECT tss.name, tss.employee, tss.employee_name
				FROM `tabSalary Slip` tss
                WHERE {conditions}
                GROUP BY tss.employee
			""", as_dict=True)
        
        return ss_sql
