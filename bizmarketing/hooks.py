app_name = "bizmarketing"
app_title = "BizMarketing"
app_publisher = "Biz Technology Solutions"
app_description = "BizMarketing System for EthioBiz"
app_email = "sovereign@ethiobiz.et"
app_license = "Proprietary"

# Apps
# ------------------

# required_apps = []
required_apps = ["frappe", "erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "bizmarketing",
# 		"logo": "/assets/bizmarketing/logo.png",
# 		"title": "BizMarketing",
# 		"route": "/bizmarketing",
# 		"has_permission": "bizmarketing.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/bizmarketing/css/bizmarketing.css"
# app_include_js = "/assets/bizmarketing/js/bizmarketing.js"

# include js, css files in header of web template
# web_include_css = "/assets/bizmarketing/css/bizmarketing.css"
# web_include_js = "/assets/bizmarketing/js/bizmarketing.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Marketing Officer": "bizmarketing-dashboard",
# 	"Marketing Manager": "bizmarketing-dashboard"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "bizmarketing.utils.jinja_methods",
# 	"filters": "bizmarketing.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "bizmarketing.install.before_install"
# after_install = "bizmarketing.install.after_install"
after_migrate = "bizmarketing.setup.create_web_forms"

# Uninstallation
# ------------

# before_uninstall = "bizmarketing.uninstall.before_uninstall"
# after_uninstall = "bizmarketing.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "bizmarketing.utils.before_app_install"
# after_app_install = "bizmarketing.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "bizmarketing.utils.before_app_uninstall"
# after_app_uninstall = "bizmarketing.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bizmarketing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"DOBiz Trial Signup": {
		"after_insert": "bizmarketing.api.dobiz_trial.setup_trial_tenant"
	},
	"Subscription": {
		"on_update": "bizmarketing.api.dobiz_trial.process_subscription_access"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"*/5 * * * *": [
			"bizmarketing.tasks.process_publishing_queue"
		],
		"0 */6 * * *": [
			"bizmarketing.tasks.fetch_engagement_metrics"
		]
	},
	"daily": [
		"bizmarketing.tasks.update_campaign_targets"
	]
}

# Testing
# -------

# before_tests = "bizmarketing.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bizmarketing.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bizmarketing.task.get_dashboard_data"
# }

# git_url = "https://github.com/biztechnology/bizmarketing"
