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
doctype_list_js = {"Attendance" : "injury/js/attendance_list.js"}
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

override_doctype_class = {
    "Salary Slip" : "masar_hrms.override._salary_slip.SalarySlip",
    "Payroll Entry" :"masar_hrms.override._payroll_entry.PayrollEntry",
    "Leave Application" : "masar_hrms.override._leave_application.LeaveApplication"
}

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
doc_events = {
	"Employee": {
		"validate": "masar_hrms.custom.employee.employee.validate",
		"on_update": "masar_hrms.custom.employee.employee.on_update"
	}
 }
doctype_js = {
   "Employee" : "custom/employee/employee.js",
   "Goal" : "custom/goal/goal.js",
   "Appraisal" : "custom/appraisal/appraisal.js",
   "Payroll Entry" : "custom/payroll_entry/payroll_entry.js"
 }

# Scheduled Tasks
# ---------------

# scheduler_events = {
	# "cron":{
	# 	"* * * * *": [
	# 		"masar_hrms.tasks.cron"
	# 	]
	# }
	# "all": [
	# 	"masar_hrms.tasks.all"
	# ],
	# "daily": [
	# 	"masar_hrms.tasks.daily"
	# ],
	# "hourly": [
	# 	"masar_hrms.tasks.hourly"
	# ],
	# "weekly": [
	# 	"masar_hrms.tasks.weekly"
	# ],
# 	"monthly": [
# 		"masar_hrms.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "masar_hrms.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates": "masar_hrms.override._payroll_entry.get_start_end_dates"
}
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
                ## Add by Mahmoud
                # Shift Type
                "Shift Type-custom_early_entry__late_exit_settings_for_overtime", 
                "Shift Type-custom_enable_early_entry_marking", 
                "Shift Type-custom_early_entry_grace_period" , 
                "Shift Type-custom_column_break_9xw3j" , 
                "Shift Type-custom_enable_late_exit_marking" , 
                "Shift Type-custom_late_exit_grace_period", 
                # Shift Assignment
                "Shift Assignment-custom_employee_shift_management", 
                # Salary Structure Assignment
                "Salary Structure Assignment-custom_scm_ref",
                "Salary Structure Assignment-change_basic_amount",
                "Salary Structure Assignment-change_amount",
                "Salary Structure Assignment-new_basic",
                "Salary Structure Assignment-change_to_date",
                "Salary Structure Assignment-change_from_date",
                "Salary Structure Assignment-old_basic",
                "Salary Structure Assignment-change_basic_amount",
                "Salary Structure Assignment-remark",
                # Salary Slip
                "Salary Slip-hourly_leaves",
                "Salary Slip-custom_work_type",
                # Salary Component
                "Salary Component-custom_is_dbr_applicable", 
                "Salary Component-is_overtime_applicable",
                "Salary Component-is_social_security_applicable",
                "Salary Component-name_ar",
                # Company
                "Company-custom_over_salary_allowance",
                "Company-custom_max_loan_duration",
                "Company-custom_dbr_percentage",
                "Company-custom_basic_salary_component",
                # Designation
                "Designation-is_hazard",
                "Designation-desi_code",
                "Designation-hazard_code",
                "Designation-column_break_2",
                "Designation-section_break_4",
                # Employee Education
                "Employee Education-custom_section_break_b9jvo",
                "Employee Education-custom_is_certificate",
                "Employee Education-custom_total_hours",
                "Employee Education-custom_issue_date",
                "Employee Education-custom_column_break_x2d6g",
                "Employee Education-custom_certificate_name",
                "Employee Education-custom_training_provider_ar",
                "Employee Education-custom_training_provider",
                "Employee Education-custom_section_break_elwxw",
                "Employee Education-custom_year_of_graduation",
                "Employee Education-custom_major_ar",
                "Employee Education-custom_major",
                "Employee Education-custom_column_break_sfiya",
                "Employee Education-custom_level_degree",
                "Employee Education-custom_universitycollege_ar",
                "Employee Education-custom_universitycollege",
                "Employee Education-custom_section_break_ooccl",
                "Employee Education-custom_remarks",
                "Employee Education-custom_column_break_mye6s",
                "Employee Education-custom_is_training",
                "Employee Education-custom_is_qualification",
                "Employee Education-custom_column_break_4caaw",
                # Employee External Work History
                "Employee External Work History-custom_from_date",
                "Employee External Work History-custom_to_date", 
                # Leave Application
                "Leave Application-custom_work_injury_ref",
                "Leave Application-custom_esla_ref",
                # Leave Type
                "Leave Type-is_short_leave",
                "Leave Type-max_short_allowed",
                "Leave Type-short_leave",
                "Leave Type-custom_is_injury",
                "Leave Type-custom_salary_deduction_rate",
                "Leave Type-custom_salary_deduction",
                # Payroll Entry
                "Payroll Entry-work_type",
                "Payroll Entry-custom_cuttoff_date",
                # Employee
                "Employee-custom_privilege_details",
                "Employee-overtime_ceiling",
                "Employee-custom_off_day_overtime_ceiling",
                "Employee-social_commity_membership",
                "Employee-association_membership_number",
                "Employee-column_break_69",
                "Employee-social_commity_fund_membership",
                "Employee-association_membership",
                "Employee-membership",
                "Employee-custom_is_engineer",
                "Employee-religion",
                "Employee-place_or_birth",
                "Employee-children_subject_to_allowance",
                "Employee-family_members",
                "Employee-family_details",
                "Employee-custom_column_break_bba4s",
                "Employee-is_overtime_applicable",
                "Employee-overtime_details",
                "Employee-custom_tax_number",        
                "Employee-bank_branch",
                "Employee-column_break_alwbp",
                "Employee-bank",
                "Employee-pobox",
                "Employee-custom_wp_end_date",
                "Employee-custom_name_of_entity",
                "Employee-custom_column_break_0htwd",
                "Employee-custom_wp_start_date",
                "Employee-custom_work_permit_number",
                "Employee-custom_work_permit_type",
                "Employee-custom_section_break_efpn4", 
                "Employee-work_type",
                "Employee-old_ref",
                "Employee-custom_id_card_no",
                "Employee-personal_no",
                "Employee-national_no",
                "Employee-nationality",
                "Employee-last_name_ar",
                "Employee-third_name_ar",
                "Employee-middle_name_ar",
                "Employee-first_name_ar",
                "Employee-full_name_ar",
                "Employee-third_name",
                "Employee-custom_employee_id",
                "Employee-custom_bank_commitment_",
                "Employee-custom_section",
                "Employee-custom_project",
                "Employee-custom_custody",
                "Employee-custom_asset_custody",
                "Employee-custom_major", 
                "Employee-custom_latest_education",
                "Employee-custom_years_at_the_company",
                "Employee-custom_ewallet",
                "Employee-custom_contract_comment",
                "Employee-basic_salary",
                "Employee-column_break_54",
                "Employee Checkin-availo",
                "custom_is_privilege_applicable",
                "Employee-custom_is_bank_commitments",
            ]
        ]
    ]},
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                    # Leave Application
                    "Leave Application-half_day-permlevel",
                    "Leave Application-status-default",
                    "Leave Application-follow_via_email-default",
                    "Leave Application-main-field_order",
                    # Employee Education
                    "Employee Education-school_univ-hidden",
                    "Employee Education-qualification-hidden",
                    "Employee Education-level-hidden",
                    "Employee Education-maj_opt_subj-hidden",
                    "Employee Education-class_per-hidden",
                    "Employee Education-year_of_passing-hidden",
                    # Employee External Work History
                    "Employee External Work History-total_experience-read_only",
                    # Employee
                    "Employee-main-field_order",
                    "Employee-internal_work_history-depends_on",
                    "Employee-naming_series-default",
                    "Employee-naming_series-options",
                    # Shift Request
                    "Shift Request-status-permlevel",
                    # Appraisal
                    "Appraisal-appraisal_kra-permlevel",
                    "Appraisal KRA-per_weightage-permlevel",
                    # Attendance
                    "Attendance-status-options",
                ]
            ]
        ]
    }
]