import frappe
from frappe import _
from frappe.utils import  get_link_to_form

class OverlappingShiftError(frappe.ValidationError):
	pass

@frappe.whitelist()
def throw_overlap_error(self, shift_details):
    shift_details = frappe._dict(shift_details)
    if shift_details.status == "Active":
        msg = _(
            "Employee {0} already has an active Shift {1}: {2} that overlaps within this period."
        ).format(
            frappe.bold(self.employee),
            frappe.bold(shift_details.shift_type),
            get_link_to_form("Shift Assignment", shift_details.name),
        )
        frappe.throw(msg, title=_("Overlapping Shifts"), exc=OverlappingShiftError)