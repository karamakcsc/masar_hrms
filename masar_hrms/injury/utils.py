from frappe.utils import getdate, today


def get_work_injury_status(docstatus, max_end_date):
	"""Derived status - Work Injury has no stored status field. A case is
	considered closed once the last (possibly extended) injury period has
	elapsed; there is no separate manual "close" action."""
	if docstatus == 0:
		return "Draft"
	if docstatus == 2:
		return "Cancelled"
	if max_end_date and getdate(max_end_date) < getdate(today()):
		return "Closed"
	return "Under Treatment"
