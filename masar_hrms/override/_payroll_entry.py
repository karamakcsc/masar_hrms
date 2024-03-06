import frappe
from frappe import _




@frappe.whitelist()
def fill_employee_details(self):
    cond  = "1=1 "
    if self.branch:
        cond += f" AND te.branch = '{self.branch}'"
    if self.designation:
        cond += f" AND te.designation = '{self.designation}'"
    if self.department:
        cond += f" AND te.department ='{self.department}' "
    if self.grade:
        cond += f" AND te.grade ='{self.grade}' "
    if self.work_type:
        cond += f" AND te.work_type ='{self.work_type}' "

    results = frappe.db.sql(f"""
        SELECT 
            te.employee ,
            te.employee_name ,
            te.department ,
            te.designation,
            te.work_type
        FROM 
            tabEmployee te 
        WHERE 
            {cond}
        """ , as_dict = True)
    
    doc = frappe.get_doc("Payroll Entry" , self.name)
    doc.number_of_employees = len(results)

    self.set("employees", [])
    attendance = []
    for result in results:
 
        attendance.append({
            "employee":result.get('employee'), 
            "employee_name":  result.get('employee_name'), 
            "department" : result.get('department'), 
            "designation" : result.get('designation')				
            })
    self.set("employees", attendance)
    self.number_of_employees = len(results)


