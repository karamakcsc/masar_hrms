import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_total_outstanding_amount():
	row = frappe.db.sql(
		"""
		SELECT SUM(per_loan.loan_amount - per_loan.repaid) AS outstanding
		FROM (
			SELECT tel.name, tel.loan_amount, IFNULL(SUM(tas.amount), 0) AS repaid
			FROM `tabEmployee Loans` tel
			LEFT JOIN `tabEmployee Loans Schedule` tels ON tels.parent = tel.name
			LEFT JOIN `tabAdditional Salary` tas ON tas.name = tels.additional_salary_ref
				AND tas.docstatus = 1
				AND tas.salary_component = 'Loan'
				AND tas.payroll_date <= CURDATE()
			WHERE tel.docstatus = 1
			GROUP BY tel.name
		) per_loan
		""",
		as_dict=True,
	)[0]

	return flt(row.outstanding or 0)
