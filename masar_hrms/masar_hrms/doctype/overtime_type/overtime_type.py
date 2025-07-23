# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OvertimeType(Document):
	
	def validate(self): 
		self.day_type_validation()
	
	def day_type_validation(self): 
		if (self.working_day + self.off_day) != 1: 
			frappe.throw("Select One of overtime Type Working Day or Off Day.")
			
