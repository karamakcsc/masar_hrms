from . import __version__ as app_version

app_name = "masar_hrms"
app_title = "Masar Hrms"
app_publisher = "KCSC"
app_description = "Masar Hrms"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@kcsc.com.jo"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/masar_hrms/css/masar_hrms.css"
# app_include_js = "/assets/masar_hrms/js/masar_hrms.js"

# include js, css files in header of web template
# web_include_css = "/assets/masar_hrms/css/masar_hrms.css"
# web_include_js = "/assets/masar_hrms/js/masar_hrms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "masar_hrms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "masar_hrms.install.before_install"
# after_install = "masar_hrms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "masar_hrms.uninstall.before_uninstall"
# after_uninstall = "masar_hrms.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "masar_hrms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	#"ToDo": "custom_app.overrides.CustomToDo"

# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }
# doc_events = {
# #  	# "Salary Slip": {
# # 	# 	"before_insert": "masar_hrms.utilities.hourly_leave_calc.SetHourlyLeaveForEmployee"
# # 	# }
#  }
doctype_js = {
   "Employee" : "custom/employee/employee.js",
   "Salary Structure Assignment" : "custom/salary_structure_assignment/salary_structure_assignment.js",
   "Salary Slip" : "custom/salary_slip/salary_slip.js",
   ############## from mahmoud 
   "Payroll Entry" : "custom/payroll_entry/payroll_entry.js", 
 }

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "cron":{
	# 	"* * * * *": [
	# 		"masar_hrms.tasks.cron"
	# 	]
	# }
	# "all": [
	# 	"masar_hrms.tasks.all"
	# ],
	"daily": [
		"masar_hrms.tasks.daily"
	]
	# "hourly": [
	# 	"masar_hrms.tasks.hourly"
	# ],
	# "weekly": [
	# 	"masar_hrms.tasks.weekly"
	# ],
	# "monthly": [
	# 	"masar_hrms.tasks.monthly"
	# ]
}

# Testing
# -------

# before_tests = "masar_hrms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "masar_hrms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "masar_hrms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"masar_hrms.auth.validate"
# ]
fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "name", "in", [
		"Employee-membership",
		"Employee-association_membership",
		"Employee-social_commity_membership",
		"Employee-social_security_number",
		"Employee-association_membership_number",
		"Employee-social_commity_fund_membership",
		"Employee-family_details",
		"Employee-family_members",
		"Employee-children_subject_to_allowance",
		"Salary Slip-hourly_leaves",
		"Employee-religion",
		"Employee-column_break_54",
		"Designation-desi_code",
		"Designation-hazard_code",
		"Designation-column_break_2",
		"Designation-section_break_4",
		"Employee-third_name",
		"Employee-first_name_ar",
		"Employee-middle_name_ar",
		"Employee-third_name_ar",
		"Employee-last_name_ar",
		"Employee-full_name_ar",
		"Employee-place_or_birth",
		"Employee-social_security_details",
		"Employee-column_break_65",
		"Employee-social_security_date",
		"Employee-column_break_69",
		"Employee-pobox",
		"Employee-nationality",
		"Employee-national_no",
		"Employee-personal_no",
		"Designation-is_hazard",
		"Salary Component-is_social_security_applicable",
		"Salary Component-name_ar",
		"Leave Type-is_short_leave",
		"Leave Type-max_short_allowed",
		"Leave Type-short_leave",
		"Employee Checkin-availo",
		"Salary Component-is_overtime_applicable",
		"Employee-is_overtime_applicable",
		"Employee-overtime_ceiling",
		"Employee-overtime_details",
		"Employee-is_social_security_applicable",
		"Employee-employee_share_rate",
		"Company-section_break_23",
		"Company-company_share_rate",
		"Company-column_break_25",
		"Company-employee_share_rate",
		"Employee-social_security_salary",
		"Employee-social_security_amount",
        "Employee-old_ref",
        "Employee-work_type",
		"Employee-tax_type",
		"Employee-bank",
		"Employee-column_break_alwbp",
		"Employee-bank_branch",
		# "Employee-iban",
		"Salary Structure Assignment-change_basic_amount",
		"Salary Structure Assignment-change_amount",
		"Salary Structure Assignment-new_basic",
        "Salary Structure Assignment-change_to_date",
        "Salary Structure Assignment-change_from_date",
        "Salary Structure Assignment-old_basic",
        "Salary Structure Assignment-change_basic_amount",
        "Salary Structure Assignment-remark",
		"Employee-basic_salary",
        "Payroll Entry-work_type",
        "Company-custom_social_security_liabilities",
        "Company-custom_social_security_expenses",
        "Company-custom_section_break_9o0od" , 
        "Shift Assignment-custom_employee_shift_management"
            ]
        ]
    ]}
]

from masar_hrms.override import _leave_application
from hrms.hr.doctype.leave_application import leave_application
from masar_hrms.override import _salary_slip
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

leave_application.get_leaves_for_period = _leave_application.get_leaves_for_period
SalarySlip.compute_taxable_earnings_for_year = _salary_slip.compute_taxable_earnings_for_year
SalarySlip.calculate_variable_tax = _salary_slip.calculate_variable_tax

from masar_hrms.override import _payroll_entry
from hrms.payroll.doctype.payroll_entry import payroll_entry
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry 
# payroll_entry.get_filter_condition= _payroll_entry.get_filter_condition
# PayrollEntry.fill_employee_detailsr = _payroll_entry.fill_employee_details
# PayrollEntry.make_filters = _payroll_entry.make_filters