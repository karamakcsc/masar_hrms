import frappe
from frappe.model.document import Document

###################### from mahmoud to create journal entry to company social security 
@frappe.whitelist()
def ss_jv(name , employee, posting_date,  payroll_entry):
    company_name         = (frappe.db.get_list("Company"))[0]['name']
    company_share_rate   = float((frappe.db.get_all("Company","company_share_rate"))[0]['company_share_rate'])
    employee_share_rate  = float((frappe.db.get_all("Company", "employee_share_rate"))[0]['employee_share_rate'])
    ss_liabilities       = frappe.db.get_all("Company", "custom_social_security_liabilities")[0]['custom_social_security_liabilities']
    ss_expenses          = frappe.db.get_all("Company", "custom_social_security_expenses")[0]['custom_social_security_expenses']
    ss_amount            = float(frappe.db.get_value("Employee", filters={'name': employee}, fieldname=["social_security_amount"]))
    ss_cost_center       = frappe.db.get_value("Payroll Entry", filters = {'name' : payroll_entry} ,fieldname = [ "cost_center"])
    ss_calculation = (ss_amount * (company_share_rate/100)) / (employee_share_rate/100)
    
    jv = frappe.new_doc("Journal Entry")
    jv.posting_date = posting_date or frappe.utils.nowdate()
    jv.company =  company_name
    jv.cost_center = ss_cost_center
    jv.cheque_no = name , 
    jv.cheque_date = posting_date,
    jv.user_remark = f"Reference Number is: {name} in Reference Date:{posting_date} "

    jv.append("accounts", {
        "account": ss_expenses,
        "debit_in_account_currency": ss_calculation,
        "cost_center": ss_cost_center,
        
        "user_remark": f"Reference Number is: {name} in Reference Date:{posting_date} "
    })

    jv.append("accounts", {
        "account": ss_liabilities,
        "credit_in_account_currency": ss_calculation,
        "cost_center": ss_cost_center,
       
        "user_remark": f"Reference Number is: {name} in Reference Date:{posting_date} "
    })

    jv.insert(ignore_permissions=True)
    jv.submit()

    return(f"Journal Entries created for{employee} in journal Entry")



############################ to subimt form payroll (subimt salary slip )
# class salary_slip(Document):
#     def on_submit(self):
#          for journal_entry in self.get("Journal Entry"):
#              ss_jv(
#                 self.employee , 
#                 self.posting_date , 
#                 self.payroll_entry
#             )