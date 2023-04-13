import math
from datetime import date

import frappe
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Sum
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_first_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
from frappe.utils.background_jobs import enqueue

import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.loan_management.doctype.loan_repayment.loan_repayment import (
	calculate_amounts,
	create_repayment_entry,
)
from erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
	process_loan_interest_accrual_for_term_loans,
)
from erpnext.utilities.transaction_base import TransactionBase

from hrms.hr.utils import get_holiday_dates_for_employee, validate_active_employee
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries
from hrms.payroll.doctype.employee_benefit_application.employee_benefit_application import (
	get_benefit_component_amount,
)
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import (
	get_benefit_claim_amount,
	get_last_payroll_period_benefits,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from hrms.payroll.doctype.salary_slip.salary_slip import calculate_tax_by_tax_slab

def calculate_variable_tax(self, tax_component):
            self.previous_total_paid_taxes = self.get_tax_paid_in_period(
                self.payroll_period.start_date, self.start_date, tax_component
            )

            # Structured tax amount
            eval_locals, default_data = self.get_data_for_eval()
            self.total_structured_tax_amount = calculate_tax_by_tax_slab(
                self.total_taxable_earnings_without_full_tax_addl_components,
                self.tax_slab,
                self.whitelisted_globals,
                eval_locals,
            )

            #self.current_structured_tax_amount =  self.total_structured_tax_amount / 12 #Yasser
            self.current_structured_tax_amount =  (
            self.total_structured_tax_amount 
            #- self.previous_total_paid_taxes
            ) / 12
            #/ self.remaining_sub_periods

            # Total taxable earnings with additional earnings with full tax
            self.full_tax_on_additional_earnings = 0.0
            if self.current_additional_earnings_with_full_tax:
                self.total_tax_amount = SalarySlip.calculate_tax_by_tax_slab(
                    self.total_taxable_earnings, self.tax_slab, self.whitelisted_globals, eval_locals
                )
                self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount

            current_tax_amount = self.current_structured_tax_amount + self.full_tax_on_additional_earnings
            if flt(current_tax_amount) < 0:
                current_tax_amount = 0

            self.component_based_veriable_tax[tax_component].update(
                {
                    "previous_total_paid_taxes": self.previous_total_paid_taxes,
                    "total_structured_tax_amount": self.total_structured_tax_amount,
                    "current_structured_tax_amount": self.current_structured_tax_amount,
                    "full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
                    "current_tax_amount": current_tax_amount,
                }
            )

            return current_tax_amount

def compute_taxable_earnings_for_year(self):
        # get taxable_earnings, opening_taxable_earning, paid_taxes for previous period
        self.previous_taxable_earnings, exempted_amount = self.get_taxable_earnings_for_prev_period(
            self.payroll_period.start_date, self.start_date, self.tax_slab.allow_tax_exemption
        )

        self.previous_taxable_earnings_before_exemption = (
            self.previous_taxable_earnings + exempted_amount
        )

        self.compute_current_and_future_taxable_earnings()

        # Deduct taxes forcefully for unsubmitted tax exemption proof and unclaimed benefits in the last period
        if self.payroll_period.end_date <= getdate(self.end_date):
            self.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
            self.deduct_tax_for_unclaimed_employee_benefits = 1

        # Get taxable unclaimed benefits
        self.unclaimed_taxable_benefits = 0
        if self.deduct_tax_for_unclaimed_employee_benefits:
            self.unclaimed_taxable_benefits = self.calculate_unclaimed_taxable_benefits()

        # Total exemption amount based on tax exemption declaration
        self.total_exemption_amount = self.get_total_exemption_amount()

        # Employee Other Incomes
        self.other_incomes = self.get_income_form_other_sources() or 0.0

        # Total taxable earnings including additional and other incomes
        if self.deduct_tax_for_unclaimed_employee_benefits == 0:
            self.total_taxable_earnings = (self.current_structured_taxable_earnings * 12) - self.total_exemption_amount # Yasser
        else:self.total_taxable_earnings = (
        	#self.previous_taxable_earnings
        	+ self.current_structured_taxable_earnings
        	+ self.future_structured_taxable_earnings
        	+ self.current_additional_earnings
        	+ self.other_incomes
        	+ self.unclaimed_taxable_benefits
        	* 12
        ) - self.total_exemption_amount

        # Total taxable earnings without additional earnings with full tax
        # self.total_taxable_earnings_without_full_tax_addl_components =(
        #     self.total_taxable_earnings - self.current_additional_earnings_with_full_tax
        self.total_taxable_earnings_without_full_tax_addl_components =(
            self.total_taxable_earnings 
        )