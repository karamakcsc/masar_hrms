# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import calendar
from datetime import date
from io import BytesIO

import frappe
from frappe import _
from frappe.model.document import Document
from pypdf import PdfWriter

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class AR3Print(Document):
    def validate(self):
        self.validate_period()
        self.set_period_dates()

    def validate_period(self):
        if not (self.month and self.year):
            frappe.throw(_("Please select both Month and Year."))

    def set_period_dates(self):
        month_index = MONTHS.index(self.month) + 1
        last_day = calendar.monthrange(self.year, month_index)[1]
        self.from_date = date(self.year, month_index, 1)
        self.to_date = date(self.year, month_index, last_day)

    @frappe.whitelist()
    def get_ss(self):
        self.set_period_dates()

        conditions = " tss.docstatus = 1 "
        conditions += " AND tss.end_date BETWEEN %(from_date)s AND %(to_date)s"
        if self.department:
            conditions += " AND tss.department = %(department)s"
        ss_sql = frappe.db.sql(
            f"""
            SELECT tss.name, tss.employee, tss.employee_name
            FROM `tabSalary Slip` tss
            WHERE {conditions}
            GROUP BY tss.employee
            """,
            {"from_date": self.from_date, "to_date": self.to_date, "department": self.department},
            as_dict=True,
        )

        return ss_sql

    @frappe.whitelist()
    def generate_pdf(self):
        if not self.print_format:
            frappe.throw(_("Please select a Print Format first."))
        if not self.ss_table:
            frappe.throw(_("Please fetch the Salary Slips first."))
        if self.pdf_status == "Processing":
            frappe.throw(_("PDF generation is already in progress."))

        self.db_set("pdf_status", "Processing", update_modified=False)

        frappe.enqueue(
            method=build_ar3_pdf,
            queue="long",
            timeout=6000,
            job_name=f"ar3_pdf_{self.name}",
            enqueue_after_commit=True,
            docname=self.name,
        )


def build_ar3_pdf(docname):
    """Render every Salary Slip linked to this AR 3 Print in the chosen Print
    Format and merge them into a single PDF, streaming pages into one
    PdfWriter instead of holding every rendered PDF in memory at once."""

    doc = frappe.get_doc("AR 3 Print", docname)
    salary_slips = [row.salary_slip for row in doc.ss_table]
    print_format = doc.print_format
    total = len(salary_slips)

    pdf_writer = PdfWriter()
    failed = []

    try:
        for idx, ss_name in enumerate(salary_slips, start=1):
            try:
                pdf_writer = frappe.get_print(
                    "Salary Slip",
                    ss_name,
                    print_format,
                    as_pdf=True,
                    output=pdf_writer,
                )
            except Exception:
                failed.append(ss_name)
                frappe.log_error(
                    title="AR 3 Print - Salary Slip PDF Generation Error",
                    message=f"Salary Slip: {ss_name}\n{frappe.get_traceback()}",
                    reference_doctype="AR 3 Print",
                    reference_name=docname,
                )

            frappe.publish_progress(
                percent=idx / total * 100,
                title=_("Generating AR 3 PDF"),
                description=_("{0}/{1} salary slips processed").format(idx, total),
                doctype="AR 3 Print",
                docname=docname,
            )

        with BytesIO() as merged_pdf:
            pdf_writer.write(merged_pdf)
            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": f"{docname}-AR3.pdf",
                    "attached_to_doctype": "AR 3 Print",
                    "attached_to_name": docname,
                    "attached_to_field": "attach_pdf",
                    "content": merged_pdf.getvalue(),
                    "is_private": 1,
                }
            )
            file_doc.save(ignore_permissions=True)

        status = "Completed" if not failed else "Failed"
        frappe.db.set_value(
            "AR 3 Print", docname, {"attach_pdf": file_doc.file_url, "pdf_status": status}
        )
        frappe.db.commit()

        frappe.publish_realtime(
            "ar3_pdf_complete",
            {
                "docname": docname,
                "file_url": file_doc.file_url,
                "status": status,
                "failed": failed,
            },
            user=frappe.db.get_value("AR 3 Print", docname, "owner"),
        )
    except Exception:
        frappe.db.set_value("AR 3 Print", docname, "pdf_status", "Failed")
        frappe.db.commit()
        frappe.log_error(
            title="AR 3 Print - PDF Generation Failed",
            reference_doctype="AR 3 Print",
            reference_name=docname,
        )
        frappe.publish_realtime(
            "ar3_pdf_complete",
            {"docname": docname, "status": "Failed"},
            user=frappe.db.get_value("AR 3 Print", docname, "owner"),
        )
