app_name = "vinod_sale_target"
app_title = "vinod_sale_target"
app_publisher = "Sukku"
app_description = "Created For report"
app_email = "sukeshanee@gmail.com"
app_license = "mit"

doctype_js = {
    "Purchase Order": "public/js/sales_invoice_weight.js",
    "Purchase Invoice": "public/js/sales_invoice_weight.js",
    "Purchase Receipt": "public/js/sales_invoice_weight.js",
    "Material Request": "public/js/sales_invoice_weight.js",
    "Stock Entry": "public/js/sales_invoice_weight.js",
    "Delivery Note": "public/js/sales_invoice_weight.js",
    "Sales Order": "public/js/sales_invoice_weight.js",
    "Quotation": "public/js/sales_invoice_weight.js",
    "Sales Invoice": "public/js/sales_invoice_weight.js"
}

doc_events = {
    "Purchase Invoice": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Purchase Order": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Purchase Receipt": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Sales Invoice": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Sales Order": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Delivery Note": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Quotation": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Material Request": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    },
    "Stock Entry": {
        "before_validate": "vinod_sale_target.weight_amount.apply_weight_based_amount"
    }
}

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Purchase Order-custom_use_weight_based_amount",
                    "Purchase Order Item-custom_weight",
                    "Purchase Invoice-custom_use_weight_based_amount",
                    "Purchase Invoice Item-custom_weight",
                    "Purchase Receipt-custom_use_weight_based_amount",
                    "Purchase Receipt Item-custom_weight",
                    "Material Request-custom_use_weight_based_amount",
                    "Material Request Item-custom_weight",
                    "Stock Entry-custom_use_weight_based_amount",
                    "Stock Entry Detail-custom_weight",
                    "Delivery Note-custom_use_weight_based_amount",
                    "Delivery Note Item-custom_weight",
                    "Sales Order-custom_use_weight_based_amount",
                    "Sales Order Item-custom_weight",
                    "Quotation-custom_use_weight_based_amount",
                    "Quotation Item-custom_weight"
                ]
            ]
        ]
    }
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vinod_sale_target",
# 		"logo": "/assets/vinod_sale_target/logo.png",
# 		"title": "vinod_sale_target",
# 		"route": "/vinod_sale_target",
# 		"has_permission": "vinod_sale_target.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vinod_sale_target/css/vinod_sale_target.css"
# app_include_js = "/assets/vinod_sale_target/js/vinod_sale_target.js"

# include js, css files in header of web template
# web_include_css = "/assets/vinod_sale_target/css/vinod_sale_target.css"
# web_include_js = "/assets/vinod_sale_target/js/vinod_sale_target.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vinod_sale_target/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vinod_sale_target/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vinod_sale_target.utils.jinja_methods",
# 	"filters": "vinod_sale_target.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vinod_sale_target.install.before_install"
# after_install = "vinod_sale_target.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vinod_sale_target.uninstall.before_uninstall"
# after_uninstall = "vinod_sale_target.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vinod_sale_target.utils.before_app_install"
# after_app_install = "vinod_sale_target.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vinod_sale_target.utils.before_app_uninstall"
# after_app_uninstall = "vinod_sale_target.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vinod_sale_target.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vinod_sale_target.tasks.all"
# 	],
# 	"daily": [
# 		"vinod_sale_target.tasks.daily"
# 	],
# 	"hourly": [
# 		"vinod_sale_target.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vinod_sale_target.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vinod_sale_target.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vinod_sale_target.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vinod_sale_target.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vinod_sale_target.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vinod_sale_target.utils.before_request"]
# after_request = ["vinod_sale_target.utils.after_request"]

# Job Events
# ----------
# before_job = ["vinod_sale_target.utils.before_job"]
# after_job = ["vinod_sale_target.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vinod_sale_target.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

