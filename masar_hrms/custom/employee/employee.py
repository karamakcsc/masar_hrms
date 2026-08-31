import frappe
from frappe import _
from frappe.utils import getdate, today, now_datetime


def validate(self, method):
    employee_full_name(self)
    education_validation(self)
    check_salaries_and_relieving_date(self)
    validate_budget_elements(self)


def on_update(self, method):
    _log_salary_table_changes(self)


def _log_salary_table_changes(employee_doc):
    try:
        before = employee_doc.get_doc_before_save()
        old_rows = {}
        if before:
            for r in (before.custom_salary_component_table or []):
                old_rows[r.salary_component] = r

        new_rows = {}
        for r in (employee_doc.custom_salary_component_table or []):
            new_rows[r.salary_component] = r

        if not old_rows and not new_rows:
            return

        posting_date = today()
        posting_time = now_datetime().strftime('%H:%M:%S')
        voucher_type = frappe.flags.get("salary_log_voucher_type") or "Employee"
        voucher_no = frappe.flags.get("salary_log_voucher_no") or employee_doc.name

        logs = []
        deactivate_for = []  # components whose previous log entries must be set is_active = 0

        for sc, new_row in new_rows.items():
            old_row = old_rows.get(sc)
            if not old_row:
                change_type = "Added"
            else:
                if (
                    float(old_row.esc_amount or 0) == float(new_row.esc_amount or 0)
                    and int(old_row.is_active or 0) == int(new_row.is_active or 0)
                    and str(old_row.date or "") == str(new_row.date or "")
                    and (old_row.remarks or "") == (new_row.remarks or "")
                ):
                    continue
                change_type = "Changed"
                deactivate_for.append(sc)

            logs.append({
                "employee": employee_doc.name,
                "employee_name": employee_doc.employee_name,
                "company": employee_doc.company,
                "department": employee_doc.department,
                "posting_date": posting_date,
                "posting_time": posting_time,
                "change_type": change_type,
                "voucher_type": voucher_type,
                "voucher_no": voucher_no,
                "salary_component": sc,
                "component_type": new_row.type or "",
                "amount": new_row.esc_amount,
                "is_active": 1,
                "effective_date": new_row.date,
                "remarks": new_row.remarks or "",
                "row_name": new_row.name,
            })

        for sc, old_row in old_rows.items():
            if sc not in new_rows:
                deactivate_for.append(sc)
                logs.append({
                    "employee": employee_doc.name,
                    "employee_name": employee_doc.employee_name,
                    "company": employee_doc.company,
                    "department": employee_doc.department,
                    "posting_date": posting_date,
                    "posting_time": posting_time,
                    "change_type": "Removed",
                    "voucher_type": voucher_type,
                    "voucher_no": voucher_no,
                    "salary_component": sc,
                    "component_type": old_row.type or "",
                    "amount": old_row.esc_amount,
                    "is_active": 0,
                    "effective_date": old_row.date,
                    "remarks": old_row.remarks or "",
                    "row_name": old_row.name,
                })
        if deactivate_for:
            placeholders = ", ".join(["%s"] * len(deactivate_for))
            frappe.db.sql(
                f"""UPDATE `tabEmployee Salary Log`
                       SET  is_active = 0
                     WHERE  employee = %s
                       AND  salary_component IN ({placeholders})
                       AND  is_active = 1""",
                [employee_doc.name] + deactivate_for,
            )

        for log_data in logs:
            frappe.get_doc({"doctype": "Employee Salary Log", **log_data}).insert(ignore_permissions=True)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Employee Salary Log Error")
    
def employee_full_name(self):
        full_name_en = None
        full_name_ar = None
        full_name_en = f"{self.first_name} {self.middle_name} {self.third_name} {self.last_name}"
        full_name_ar = f"{self.first_name_ar} {self.middle_name_ar} {self.third_name_ar} {self.last_name_ar}"
        if full_name_en:
            self.employee_name = full_name_en
        if full_name_ar:
            self.full_name_ar = full_name_ar
            
def validate_budget_elements(self):
    if self.custom_employee_budget_element:
        budgeting_type = frappe.db.get_value(
            "Budget Element", self.custom_employee_budget_element, "budgeting_type", cache=True
        )
        if budgeting_type not in ("L", "L1", "L2" , "S"):
            frappe.throw(
                _(
                    "Employee Budget Element {0} has Budgeting Type {1}. "
                    "Only Budget Elements with Budgeting Type L, L1, L2 or S can be selected."
                ).format(
                    frappe.bold(self.custom_employee_budget_element),
                    frappe.bold(budgeting_type or _("Not Set")),
                )
            )


def education_validation(self):
    for e in self.education:
        if e.custom_is_qualification and e.custom_is_training:
            frappe.throw("You can't select both Qualification and Training for the same Education record.")
            
           
def check_salaries_and_relieving_date(self):
    sql = frappe.db.sql(f'''
        SELECT 
            MAX(tss.end_date ) 
        FROM 
            `tabSalary Slip` tss 
        WHERE 
            tss.employee = '{self.name}' 
            AND tss.docstatus = 1 
            AND tss.end_date IS NOT NULL
    ''', as_list=1)
    if sql and sql[0][0] and self.relieving_date and getdate(self.relieving_date) < getdate(sql[0][0]):
        frappe.throw(f"Relieving date cannot be before the end date of the last salary slip.<br> Last salary slip end date: <b>{sql[0][0]}</b>")