# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import get_doc , db , _ , throw , bold

class SalaryComponentManagement(Document):
	@frappe.whitelist()
	def get_exist_setting_from_employee(self , employee = None):
		if not employee: 
			self.update({
			"is_ss_applicable":0,
			"is_hazard" :0,
			"social_security_number" : None, 
			"tax_type" : None,
			"ss_date" :None, 
			"is_overtime_applicable" :0, 
			"overtime_ceiling" : 0 , 
			"basic_salary" : 0 , 
			"components" : []
		})
			self.calculate_salry_details_section()
			return 1
		emp_doc  , basic_salary_component  , basic_salary= get_doc('Employee' , self.employee) , None , 0 
		components = list()
		for r in emp_doc.custom_salary_component_table:
			if r.salary_component == db.get_value('Company' , self.company , 'custom_basic_salary_component') and r.is_active == 1: 
				basic_salary_component , basic_salary , b_from_date = r.salary_component , r.esc_amount , r.date
			elif r.is_active == 1: 
				components.append({
					"salary_component" : r.salary_component, 
					"amount" : r.esc_amount , 
					"remarks": r.remarks , 
					"from_date" : r.date
				})
		self.update({
			"is_ss_applicable":emp_doc.is_social_security_applicable,
			"is_hazard" : emp_doc.custom_is_hazard,
			"social_security_number" : emp_doc.social_security_number, 
			"tax_type" : emp_doc.tax_type,
			"ss_date" : emp_doc.social_security_date, 
			"is_overtime_applicable" : emp_doc.is_overtime_applicable, 
			"overtime_ceiling" : emp_doc.overtime_ceiling , 
			"basic_salary_component" : basic_salary_component,
			"basic_salary" : basic_salary , 
			"b_from_date" : b_from_date,
			"components" : components , 
			"tax_number": emp_doc.custom_tax_number
		})
		self.calculate_salry_details_section()
		return 1 

	@frappe.whitelist()
	def calculate_salry_details_section(self): 
		ss_rate = db.get_value('Company' , self.company , 'employee_share_rate')
		total_earning = total_deduction = ss_salry = ss_amount = 0 
		total_earning  , ss_salry = self.basic_salary , self.basic_salary
		for c in self.components: 
			c_type = db.get_value('Salary Component' , c.salary_component , 'type')
			if c_type == 'Earning':
				total_earning += c.amount
				if db.get_value('Salary Component' , c.salary_component , 'is_social_security_applicable'):
					ss_salry += c.amount
			elif c_type == 'Deduction': 
				total_deduction += c.amount
		# if self.edit_ss_salary == 0: 
		# 	self.social_security_salary = ss_salry
		self.earning_salary = total_earning
		self.deduction_salary = total_deduction
		# self.social_security_amount = self.social_security_salary * ss_rate /100


	def check_scm_exists_date(self):
		exist_scm = db.sql("""
                                SELECT 
                                    name , from_date
                                FROM 
                                    `tabSalary Component Management` tescm 
                                WHERE 
                                    from_date >= %s 
                                    AND employee = %s 
                                    AND docstatus =1  
                                    AND name != %s
        """  , (self.from_date , self.employee , self.name) , as_dict = True)
		if len(exist_scm) != 0 :
			throw(
                """
                This employee already has <b>{name}</b> from date <b>{date}</b>. <br> 
                Start date cannot be earlier than that.
                """
                .format(emp = self.employee , name = exist_scm[0]['name'] , date = str(exist_scm[0]['from_date'])),
                title = _("Exist SCM")
                )		
	def ckeck_basic_component_and_ss_componet(self):
		for r in self.components: 
			if r.salary_component == self.basic_salary_component: 
				throw(f"Salary Component {bold(r.salary_component)} can not be in table and Basic Salary Component at the same time")
    
		if not self.basic_salary or self.basic_salary <= 0:
			throw("Basic salary cannot be zero.", title=_("Validation Error"))

		# if self.is_ss_applicable and self.social_security_salary <= 0:
		# 	throw("Social Security Salary cannot be zero.", title=_("Validation Error"))

	def validate(self): 
		self.check_scm_exists_date()
		self.ckeck_basic_component_and_ss_componet()

	def on_submit(self): 
		self.effect_employee_date()
		self.add_history()
		if self.create_assignment ==1: 
			self.create_ssa()
	def get_salary_components(self):
		sc_tab = [{
		"salary_component" : self.basic_salary_component , 
		"is_active" : 1 , 
		"esc_amount" : self.basic_salary , 
		"date" : self.b_from_date , 
		"remarks" : "Basic Salary Component"
		}]
		for r in self.components: 
			sc_tab.append({
			"salary_component" : r.salary_component , 
			"is_active" : 1 , 
			"esc_amount" : r.amount , 
			"date" : r.from_date , 
			"remarks" : r.remarks
			})
		return sc_tab
	def effect_employee_date(self): 
		emp_doc = get_doc('Employee' , self.employee)
		sc_tab = self.get_salary_components()
		emp_doc.update({
			"is_social_security_applicable": self.is_ss_applicable,
       		"custom_is_hazard" : self.is_hazard,
			"social_security_number" : self.social_security_number, 
			"tax_type" : self.tax_type,
			"social_security_date" : self.ss_date, 
			# "social_security_salary" : self.social_security_salary, 
			# "social_security_amount" : self.social_security_amount,
			"is_overtime_applicable" : self.is_overtime_applicable, 
			"overtime_ceiling" : self.overtime_ceiling , 
			"custom_salary_component_table" : sc_tab , 
   			"custom_tax_number" : self.tax_number,
   
		}).save()
	def define_html_component(self):
		style = """
                    <style>
                .wide-table { width: 100%; }
                .first-column { width: 40%;}
                .text-right {text-align: right; }
            </style>
        """
		html = """  <div class="container mt-3">"""
		html+= """      <table class="table table-bordered table-hover wide-table">"""
		html+= """          <thead class="thead-light"> """
		html+= """              <tr> """
		html+= """                  <th scope="col" class="first-column">Salary Component</th>"""
		html+= """                  <th scope="col" class="text-right">Amount</th> """
		html+= """                  <th scope="col" class="text-right">Remarks</th> """
		html+= """                  <th scope="col" class="text-right">From Date</th> """  
		html+= """              </tr> """ 
		html+= """          </thead> """
		html += "           <tbody>"
		for sal in self.components:
			html += "           <tr>"
			html += f"              <td>{sal.salary_component}</td>"
			html += f"""            <td class="text-right">{sal.amount}</td>"""
			html += f"""            <td class="text-right">{sal.remarks}</td>"""
			html += f"""            <td class="text-right">{sal.from_date}</td>"""
			html += "           </tr>"
		html += "           </tbody>"
		html += """     </table>
  					</div>"""
		code = style + html
		return code 
   
	def add_history(self): 
		exist_emp = frappe.db.sql("""
                SELECT 
                    name 
                FROM 
                    `tabSalary Component History` tesch 
                WHERE 
                    employee = %s 
        """ , (self.employee) , as_dict = True )
		if len(exist_emp) != 0:
			history_doc = frappe.get_doc('Salary Component History' , exist_emp[0]['name'])
		else:
			history_doc = frappe.new_doc('Salary Component History')
			history_doc.employee = self.employee
			history_doc.employee_name = self.employee_name 
			history_doc.company = self.company
			history_doc.department = self.department

            
		for row in history_doc.history  : 
			row.is_active = 0     
            
		html = self.define_html_component()
		data= frappe._dict({
                "is_active" : 1,
                "from_date" : self.from_date, 
                "salary_component_management" : self.name,
                "is_ss_applicable" : self.is_ss_applicable, 
                "is_hazard" : self.is_hazard, 
                "social_security_number" : self.social_security_number, 
                "tax_type" : self.tax_type, 
                "ss_date" : self.ss_date, 
                "basic_salary_component": self.basic_salary_component,
                "basic_salary" : self.basic_salary,
                "b_from_date" : self.b_from_date, 
                "is_overtime_applicable" : self.is_overtime_applicable, 
                "overtime_ceiling" : self.overtime_ceiling, 
                "editor" : html,
                "earning_salary" : self.earning_salary, 
                "deduction_salary" : self.deduction_salary,
                # "edit_ss_salary" : self.edit_ss_salary,
                # "social_security_salary" : self.social_security_salary,
                # "social_security_amount" : self.social_security_amount,
                "tax_number": self.tax_number,
                "create_assignment" : self.create_assignment , 
                "salary_structure" : self.salary_structure, 
                "ssa_from_date" : self.ssa_from_date, 
                "income_tax_slab" : self.income_tax_slab
        })
		history_doc.append('history' , data)
		sc_tab = self.get_salary_components()
		for row in history_doc.components  : 
			row.is_active = 0
		for c in sc_tab: 
			history_doc.append('components' , {
				"salary_component" : c.get('salary_component') , 
				"is_active" : c.get("is_active") , 
				"amount" : c.get("esc_amount") , 
				"from_date" : c.get("date") , 
				"remarks" : c.get("remarks") , 
				"salary_component_management" : self.name
			})
		history_doc.save()

	def create_ssa(self): 
		data = {
			"employee" : self.employee ,
			"salary_structure" : self.salary_structure , 
			"company" : self.company, 
   			"from_date" : self.ssa_from_date, 
			"income_tax_slab" : self.income_tax_slab , 
			"custom_scm_ref" : self.name 
		}       
		frappe.new_doc('Salary Structure Assignment').update(data).save().submit()
        
        
        
        