from __future__ import unicode_literals
import frappe, erpnext
from frappe.utils import flt, cstr, nowdate, comma_and
from frappe import throw, msgprint, _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def p_before_submit(self, method):
    set_cheque_status(self)

def p_on_submit(self, method):
    add_cheque(self)

def p_on_cancel(self, method):
    delete_cheque(self)
    
def validate(self, method):
    employee_full_name(self)

def set_cheque_status(self):
    if self.mode_of_payment == "Cheque":
            if self.payment_type == "Receive":
                for d in self.get("payment_cheques"):
                    acc_doc = frappe.get_doc("Account", d.paid_to)

                    #Cash
                    if acc_doc.account_type == "Cash":
                        d.cheque_status = "Received"

                    #Bank
                    if acc_doc.account_type == "Bank":
                        d.cheque_status = "Collected"

                    #Under Collection
                    if acc_doc.under_collection == 1:
                        d.cheque_status = "Under Collection"
            if self.payment_type == "Pay":
                for d in self.get("payment_cheques"):
                    acc_doc = frappe.get_doc("Account", d.paid_from)

                    #Bank
                    if acc_doc.account_type == "Bank":
                        d.cheque_status = "Paid"

                    #Post-Dated-Cheque
                    if acc_doc.post_dated_cheque == 1:
                        d.cheque_status = "Post-Dated Cheque"


def add_cheque(self):
     for d in self.get("payment_cheques"):
         if not frappe.db.exists("Cheque", d.parent + "-" + d.cheque_no):
             acc_doc = frappe.get_doc("Account", d.paid_from)
             doc = frappe.new_doc('Cheque')
             doc.payment_entry = d.name
             doc.cheque_no = d.cheque_no
             doc.payment_type = d.payment_type
             doc.cheque_value_date = d.cheque_value_date
             doc.cheque_bank = d.cheque_bank
             doc.cheque_amount = d.cheque_amount
             doc.party_type = d.party_type
             doc.party = d.party
             doc.cheque_status = d.cheque_status
             doc.paid_from = d.paid_from
             doc.paid_to = d.paid_to
             doc.paid_from_account_currency = d.paid_from_account_currency
             doc.paid_to_account_currency = d.paid_to_account_currency
             if d.payment_type == 'Pay' and acc_doc.post_dated_cheque == 1:
                 doc.current_account = d.paid_from
             else:
                 doc.current_account = d.paid_to
             doc.insert()

def delete_cheque(self):
     for d in self.get("payment_cheques"):
        if frappe.db.exists("Cheque", d.parent + "-" + d.cheque_no):
            cheque_doc = frappe.get_doc("Cheque", d.parent + "-" + d.cheque_no)
            cheque_doc.delete()



#### from mahmoud to get full name to employee 

    
    
def employee_full_name(self):
        full_name_en = None
        full_name_ar = None
    
    # if self.first_name and self.middle_name and self.third_name and self.last_name:
        full_name_en = f"{self.first_name} {self.middle_name} {self.third_name} {self.last_name}"
    # else:
    #     frappe.throw("Please set the employee's full name")
    # if self.first_name_ar and self.middle_name_ar and self.third_name_ar and self.last_name_ar:
        full_name_ar = f"{self.first_name_ar} {self.middle_name_ar} {self.third_name_ar} {self.last_name_ar}"
    # else:
    #     frappe.throw("Please set the employee's arabic full name")
    
        if full_name_en:
            self.employee_name = full_name_en
        if full_name_ar:
            self.full_name_ar = full_name_ar