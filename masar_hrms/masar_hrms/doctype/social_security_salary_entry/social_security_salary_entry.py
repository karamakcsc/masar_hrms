# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document

class SocialSecuritySalaryEntry(Document):
	pass 
			
@frappe.whitelist()
def fill_employee_details( department = None,  branch = None , designation = None ):
	condition = ""
	values =[]
	if department:
		condition = "AND department = %s"
		values.append(department)
	if branch:
		condition = "AND branch = %s"
		values.append(branch)
	if designation:
		condition = "AND designation = %s"
		values.append(designation)	
	sql_query = f"""
        SELECT name , employee_name , department , branch , designation 
        FROM tabEmployee te 
        WHERE 1=1
        {condition}
    """
	sql_result = frappe.db.sql(sql_query, tuple(values), as_dict=True)
	return sql_result




@frappe.whitelist()
def create_employee_social_security_salary(name , posting_date):
	employee_sql = frappe.db.sql("""
		SELECT tssed.employee 
			FROM `tabSocial Security Salary Entry` tssse 
			INNER JOIN `tabSocial Security Employee Detail` tssed  ON tssse.name = tssed.parent 
			WHERE tssed.parent  = %s
	""" , (name))


	exist = frappe.db.sql("""
		SELECT employee , docstatus
			FROM `tabEmployee Social Security Salary` tesss 
		""")
	employee_name = [name[0] for name in  employee_sql]
	exist_employee = [name[0] for name in exist]
	status = [doc[1] for doc in exist]
	len_status = len(status)
	range_status = 0 
	for new_employee_ss in employee_name:
		if (new_employee_ss in exist_employee and status[range_status] == 1  ):
			if(range_status < len_status):
				range_status =+1 
		else:	
			doc = frappe.new_doc("Employee Social Security Salary")
			doc.employee = new_employee_ss
			doc.posting_date = posting_date
			doc.insert(ignore_permissions=True)
			doc.save()
			calcutale_all_share(new_employee_ss , doc)
			
	if exist_employee == []:
		return f'The Employee Social Security Salary is created For All Employee.'
	else:
		return f'The Employee Social Security Salary is created For All Employee Except The Employees : {exist_employee} Becuase Alredy Created '
			
@frappe.whitelist()
def calcutale_all_share(employee  , doc ):
	result = frappe.db.sql("""
		SELECT 
			tesss.company_share_rate, 
			tesss.employee_share_rate,
			tssa.base,
			COALESCE(SUM(tsd.amount), 0) AS Earnings 
		FROM 
			`tabEmployee Social Security Salary` tesss 
			INNER JOIN `tabSalary Structure Assignment` tssa ON tesss.employee  = tssa.employee 
			INNER JOIN `tabSalary Structure` tss ON tssa.salary_structure  = tss.name 
			INNER JOIN `tabSalary Detail` tsd ON tss.name = tsd.parent AND tsd.parentfield = 'earnings'
			INNER JOIN `tabSalary Component` tsc ON tsd.salary_component = tsc.name
		WHERE
			 tesss.employee = %s
			 AND tssa.docstatus = 1 
			 AND tsc.is_social_security_applicable =1 
		GROUP BY 
			tesss.company_share_rate, 
			tesss.employee_share_rate,
			tssa.base;
	""" , (employee) , as_dict=True)

	company_share_rate = result[0]['company_share_rate']
	employee_share_rate = result[0]['employee_share_rate'] 
	base_salary = result[0]['base']
	earnings = result[0]['Earnings']

	company_share = (base_salary + earnings ) * (company_share_rate/100)
	employee_share = (base_salary + earnings ) * (employee_share_rate/100)
	doc.ss_company_share_amount = company_share
	doc.ss_emp_share_amount = employee_share
	doc.amount = (base_salary + earnings )
	doc.save()
	doc.submit()