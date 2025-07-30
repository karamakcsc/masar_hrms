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
        self.total_loan_validate()
        self.max_loan_months_validate()
        self.contract_end_date_validate()
        self.dbr_validate()
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
            if self.start_this_month:
                total_months += 1
            self.total_months = total_months
        if self.repayment_method == "Custom Monthly Amount":    
            if not self.start_date:
                frappe.throw("Please set Loan Start Date.")
                
    def set_repayment_amount(self):
        if not self.loan_amount:
            frappe.throw("Please set both Loan Amount and Total Months.")
        
        if self.repayment_method == "Equal Monthly Installments":
            monthly_amount = self.loan_amount / self.total_months
            self.repayment_amount_month = round(monthly_amount, 3)
        elif self.repayment_method == "Custom Monthly Amount":
            if not self.repayment_amount_month:
                frappe.throw("Please set the Repayment Amount per Month.")
            if self.repayment_amount_month > self.loan_amount:
                frappe.throw("Repayment Amount per Month cannot be greater than Loan Amount.")
            monthly_amount = self.repayment_amount_month
            if self.start_date and monthly_amount:
                months = round(self.loan_amount / monthly_amount)
                self.total_months = months
                if not self.start_this_month:
                    months += 1
                self.end_date = get_last_day(add_months(getdate(self.start_date), months - 1))
    
    def max_loan_months_validate(self):
        max_total_months = frappe.db.get_value("Company", self.company, "custom_max_loan_duration")
        if not max_total_months:
            frappe.throw("Please set the Maximum Loan Duration in Company settings.")
        if self.total_months:
            if self.total_months > max_total_months:
                frappe.throw(f"Total Months {self.total_months} exceeds Maximum Loan Duration {max_total_months} months. Please adjust the loan duration or check the Company settings.")
    
    def dbr_validate(self):
        dbr_percentage = frappe.db.get_value("Company", self.company, "custom_dbr_percentage")
        if not dbr_percentage:
            frappe.throw("Please set the DBR Percentage in Company settings.")
        if self.employee:
            emp_doc = frappe.get_doc("Employee", self.employee)
            earining_salary = 0
            deduction_salary = 0
            for comp in emp_doc.custom_salary_component_table:
                if comp.is_active:
                    if comp.type:
                        if comp.type == "Earning":
                            earining_salary += comp.esc_amount
                        if comp.type == "Deduction":
                            deduction_salary += comp.esc_amount
                    else:
                        comp_doc = frappe.get_doc("Salary Component", comp.salary_component)
                        if comp_doc.type == "Earning":
                            earining_salary += comp.esc_amount
                        if comp_doc.type == "Deduction":
                            deduction_salary += comp.esc_amount
            total_salary = earining_salary - deduction_salary
            dbr_salary = (total_salary * dbr_percentage) / 100
            if self.repayment_amount_month > dbr_salary:
                frappe.throw(f"Loan Repayment Amount {self.repayment_amount_month} exceeds DBR Salary {dbr_salary}. Please adjust the repayment amount or check the DBR settings in Company.")
    
    def total_loan_validate(self):
        over_allowance_percent = frappe.db.get_value("Company", self.company, "custom_over_salary_allowance")
        if not over_allowance_percent:
            frappe.throw("Please set the Over Salary Restriction in Company settings.")
        if self.employee:
            emp_doc = frappe.get_doc("Employee", self.employee)
            earining_salary = 0
            for comp in emp_doc.custom_salary_component_table:
                if comp.is_active:
                    if comp.type:
                        if comp.type == "Earning" and comp_doc.is_social_security_applicable:
                            earining_salary += comp.esc_amount
                    else:
                        comp_doc = frappe.get_doc("Salary Component", comp.salary_component)
                        if comp_doc.type == "Earning" and comp_doc.is_social_security_applicable:
                            earining_salary += comp.esc_amount
            total_salary = earining_salary
            osa_salary = (total_salary * over_allowance_percent) / 100
            if self.loan_amount > osa_salary:
                frappe.throw(f"Loan amount {self.loan_amount} exceeds over salary allowance {osa_salary}. Please adjust the loan amount or check the OSA settings in Company.")
        
        
    def contract_end_date_validate(self):
        if self.contract_end_date:
            if self.start_date and getdate(self.start_date) > getdate(self.contract_end_date):
                frappe.throw(f"Loan Start Date {self.start_date} cannot be after Contract End Date {self.contract_end_date}.")
            if self.end_date and getdate(self.end_date) > getdate(self.contract_end_date):
                frappe.throw(f"Loan End Date {self.end_date} cannot be after Contract End Date {self.contract_end_date}.")
    
    def create_loan_schedule(self):
        self.loans_schedule = []

        if not self.loan_amount or not self.total_months:
            frappe.throw("Please set both Loan Amount and Total Months.")

        base_monthly = round(self.repayment_amount_month, 3)
        accumulated = 0
        start_date = getdate(self.start_date)

        if self.start_this_month:
            schedule_base = start_date.replace(day=1)
        else:
            schedule_base = add_months(start_date.replace(day=1), 1)
            
        for i in range(self.total_months):
            payment_date = get_last_day(add_months(schedule_base, i))

            if i == self.total_months - 1:
                repayment = round(self.loan_amount - accumulated, 3)
            else:
                repayment = base_monthly

            accumulated += repayment

            self.append("loans_schedule", {
                "schedule_date": payment_date,
                "repayment_amount": repayment,
                "accumulated_repayment_amount": round(accumulated)
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
                frappe.throw(f"Employee: {self.employee} already has loan repayments scheduled between {min_date} and {max_date}. Please create it in Employee Loans Management.")
    
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
            self.save(ignore_permissions=True)
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