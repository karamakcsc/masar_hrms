# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, get_last_day, getdate
from dateutil.relativedelta import relativedelta


class EmployeeLoans(Document):
    def validate(self):
        self.set_loan_months()
        self.set_repayment_amount()
        self.create_loan_schedule()
    def on_submit(self):
        self.validate_loan_schedule()
        self.create_additional_salary()
    
    
    def set_loan_months(self):
        if not self.repayment_method:
            frappe.throw("Please select a Repayment Method.")
        
        if self.repayment_method == "Equal Monthly Installments":    
            if not self.start_date or not self.end_date:
                frappe.throw("Please set both Loan Start Date and Loan End Date.")
                
            start_date = getdate(self.start_date)
            end_date = getdate(self.end_date)
        
            if start_date > end_date:
                frappe.throw("Loan Start Date cannot be after Loan End Date.")
        
            total_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
            self.total_months = total_months
        
    def set_repayment_amount(self):
        if not self.loan_amount:
            frappe.throw("Please set both Loan Amount and Total Months.")
        
        if self.repayment_method == "Equal Monthly Installments":
            monthly_amount = self.loan_amount / self.total_months
            self.repayment_amount_month = round(monthly_amount, 3)
        elif self.repayment_method == "Custom Monthly Amount":
            if not self.repayment_amount_month:
                frappe.throw("Please set the Repayment Amount per Month.")
            monthly_amount = self.repayment_amount_month
            self.total_months = round((self.loan_amount / monthly_amount))
    
    def create_loan_schedule(self):
        self.loans_schedule = []

        if not self.loan_amount or not self.total_months:
            frappe.throw("Please set both Loan Amount and Total Months.")

        base_monthly = round(self.repayment_amount_month, 3)
        accumulated = 0

        for i in range(self.total_months):
            payment_date = get_last_day(add_months(self.start_date, i + 1))

            if i == self.total_months - 1:
                repayment = round(self.loan_amount - accumulated, 3)
            else:
                repayment = base_monthly

            accumulated += repayment

            self.append("loans_schedule", {
                "schedule_date": payment_date,
                "repayment_amount": repayment,
                "accumulated_repayment_amount": accumulated
            })
    
    def validate_loan_schedule(self):
        existing_loans = frappe.db.sql("""
            SELECT 
                MIN(tels.schedule_date) AS min_date,
                MAX(tels.schedule_date) AS max_date
            FROM `tabEmployee Loans` AS tel
            INNER JOIN `tabEmployee Loans Schedule` AS tels ON tels.parent = tel.name
            WHERE
                tel.employee = %s
                AND tel.docstatus = 1
                AND tel.name != %s
        """, (self.employee, self.name), as_dict=True)
        
        if existing_loans and existing_loans[0].min_date and existing_loans[0].max_date:
            min_date = existing_loans[0].min_date
            max_date = existing_loans[0].max_date
        
        overlapping_dates = []
        for loan in self.loans_schedule:
            if min_date <= loan.schedule_date <= max_date:
                overlapping_dates.append(loan.schedule_date)
                
        if overlapping_dates:
            frappe.throw(f"Employee: {self.employee} already has loan repayments scheduled between {min_date} and {max_date}. Please adjust the loan period to avoid overlapping repayment dates.")
    
    def create_additional_salary(self):
        if self.loans_schedule:
            for loan in self.loans_schedule:
                additional_salary = frappe.new_doc("Additional Salary")
                additional_salary.employee = self.employee
                additional_salary.employee_name = self.employee_name
                additional_salary.department = self.department
                additional_salary.company = self.company
                additional_salary.is_recurring = 0
                additional_salary.payroll_date = loan.schedule_date
                additional_salary.salary_component =  "Loan"
                additional_salary.type  = "Deduction"
                additional_salary.amount =  loan.repayment_amount
                additional_salary.deduct_full_tax_on_selected_payroll_date =  1
                additional_salary.overwrite_salary_structure_amount = 1
                additional_salary.ref_doctype = self.doctype
                additional_salary.ref_docname = self.name
                additional_salary.insert(ignore_permissions=True)
                additional_salary.submit()
                loan.additional_salary_ref = additional_salary.name
            frappe.msgprint(f"Additional Salary created for Employee {self.employee}", alert=True, indicator='green')
        

    @frappe.whitelist()
    def get_basic_salary(self):
        emp_doc = frappe.get_doc("Employee", self.employee)
        co_doc = frappe.get_doc("Company", self.company)
        basic_salary_component = co_doc.custom_basic_salary_component
        for component in emp_doc.custom_salary_component_table:
            if component.salary_component == basic_salary_component and component.is_active:
                self.basic_salary = component.esc_amount
                return component.esc_amount
        return False