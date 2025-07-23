import frappe

def validate(self, method):
    employee_full_name(self)
#### from mahmoud to get full name to employee     
def employee_full_name(self):
        full_name_en = None
        full_name_ar = None
        full_name_en = f"{self.first_name} {self.middle_name} {self.third_name} {self.last_name}"
        full_name_ar = f"{self.first_name_ar} {self.middle_name_ar} {self.third_name_ar} {self.last_name_ar}"
        if full_name_en:
            self.employee_name = full_name_en
        if full_name_ar:
            self.full_name_ar = full_name_ar