import frappe

def validate(self, method):
    employee_full_name(self)
    education_validation(self)
    
def employee_full_name(self):
        full_name_en = None
        full_name_ar = None
        full_name_en = f"{self.first_name} {self.middle_name} {self.third_name} {self.last_name}"
        full_name_ar = f"{self.first_name_ar} {self.middle_name_ar} {self.third_name_ar} {self.last_name_ar}"
        if full_name_en:
            self.employee_name = full_name_en
        if full_name_ar:
            self.full_name_ar = full_name_ar
            
def education_validation(self):
    for e in self.education:
        if e.custom_is_qualification and e.custom_is_training:
            frappe.throw("You can't select both Qualification and Training for the same Education record.")
            