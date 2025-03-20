import frappe


@frappe.whitelist()
def get_emp(user):
    emp_sql = frappe.db.sql("""
            SELECT name FROM tabEmployee WHERE user_id = %s
        """, (user), as_dict=True)
    
    if emp_sql and emp_sql[0] and emp_sql[0]['name']:
        return emp_sql[0]['name']
    
@frappe.whitelist()
def get_manager(emp):
    manager_sql = frappe.db.sql("""
            SELECT reports_to FROM tabEmployee WHERE name = %s
        """, (emp), as_dict=True)
    
    manager_user = frappe.db.sql("""
            SELECT user_id FROM tabEmployee WHERE name = %s
        """, (manager_sql[0]['reports_to']), as_dict=True)
    
    if manager_user and manager_user[0] and manager_user [0]['user_id']:
        return manager_user [0]['user_id']