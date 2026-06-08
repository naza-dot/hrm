"""
horilla/config.py

Horilla app configurations
"""

import importlib
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth.context_processors import PermWrapper

from horilla.horilla_apps import SIDEBARS

logger = logging.getLogger(__name__)


def get_apps_in_base_dir():
    return SIDEBARS


def import_method(accessibility):
    module_path, method_name = accessibility.rsplit(".", 1)
    module = __import__(module_path, fromlist=[method_name])
    accessibility_method = getattr(module, method_name)
    return accessibility_method


ALL_MENUS = {}

SAAS_SIDEBAR_MENUS = [
    {
        "menu": "Dashboard",
        "app": "saas_admin_dashboard",
        "img_src": "images/ui/dashboard.svg",
        "submenu": [
            {"menu": "Overview", "redirect": "/saas-admin/dashboard"},
        ],
    },
    {
        "menu": "Tenant Management",
        "app": "tenant_management",
        "img_src": "images/ui/dashboard.svg",
        "submenu": [
            {"menu": "All Companies", "redirect": "/saas-admin/dashboard?tab=all-companies"},
            {"menu": "Pending Companies", "redirect": "/saas-admin/dashboard?tab=pending-companies"},
            {"menu": "Suspended Companies", "redirect": "/saas-admin/dashboard?tab=suspended-companies"},
        ],
    },
    {
        "menu": "User Management",
        "app": "user_management",
        "img_src": "images/ui/employees.svg",
        "submenu": [
            {"menu": "Platform Users", "redirect": "/saas-admin/dashboard?tab=platform-users"},
            {"menu": "Roles & Permissions", "redirect": "/saas-admin/dashboard?tab=roles-permissions"},
        ],
    },
    {
        "menu": "Subscription & Billing",
        "app": "subscription_billing",
        "img_src": "images/ui/wallet-outline.svg",
        "submenu": [
            {"menu": "Plans", "redirect": "/saas-admin/dashboard?tab=plans"},
            {"menu": "Payments", "redirect": "/saas-admin/dashboard?tab=payments"},
            {"menu": "Invoices", "redirect": "/saas-admin/dashboard?tab=invoices"},
        ],
    },
    {
        "menu": "Analytics",
        "app": "analytics",
        "img_src": "images/ui/report.svg",
        "submenu": [
            {"menu": "Platform Metrics", "redirect": "/saas-admin/dashboard?tab=platform-metrics"},
            {"menu": "Revenue Reports", "redirect": "/saas-admin/dashboard?tab=revenue-reports"},
            {"menu": "User Growth", "redirect": "/saas-admin/dashboard?tab=user-growth"},
        ],
    },
    {
        "menu": "System Monitoring",
        "app": "system_monitoring",
        "img_src": "images/ui/notification.svg",
        "submenu": [
            {"menu": "Logs", "redirect": "/saas-admin/dashboard?tab=logs"},
            {"menu": "Error Tracking", "redirect": "/saas-admin/dashboard?tab=error-tracking"},
            {"menu": "Activity Audit", "redirect": "/saas-admin/dashboard?tab=activity-audit"},
        ],
    },
    {
        "menu": "Configuration",
        "app": "configuration",
        "img_src": "images/ui/cog.svg",
        "submenu": [
            {"menu": "Global Settings", "redirect": "/saas-admin/dashboard?tab=global-settings"},
            {"menu": "Email Templates", "redirect": "/saas-admin/dashboard?tab=email-templates"},
            {"menu": "Integrations", "redirect": "/saas-admin/dashboard?tab=integrations"},
        ],
    },
    {
        "menu": "Support Center",
        "app": "support_center",
        "img_src": "images/ui/headset-solid.svg",
        "submenu": [
            {"menu": "Tickets", "redirect": "/saas-admin/dashboard?tab=tickets"},
            {"menu": "Customer Requests", "redirect": "/saas-admin/dashboard?tab=customer-requests"},
        ],
    },
    {
        "menu": "Security",
        "app": "security",
        "img_src": "images/ui/dashboard.svg",
        "submenu": [
            {"menu": "Access Control", "redirect": "/saas-admin/dashboard?tab=access-control"},
            {"menu": "MFA Settings", "redirect": "/saas-admin/dashboard?tab=mfa-settings"},
        ],
    },
    {
        "menu": "Backups",
        "app": "backups",
        "img_src": "images/ui/dashboard.svg",
        "submenu": [
            {"menu": "Backups", "redirect": "/saas-admin/dashboard?tab=backups"},
        ],
    },
]


def sidebar(request):

    base_dir_apps = get_apps_in_base_dir()

    if not request.user.is_anonymous:
        request.MENUS = []
        MENUS = request.MENUS

        if getattr(request.user, "is_saas_admin", False):
            for menu in SAAS_SIDEBAR_MENUS:
                MENU = {
                    "menu": menu["menu"],
                    "app": menu["app"],
                    "img_src": menu["img_src"],
                    "submenu": [
                        {"menu": item["menu"], "redirect": item["redirect"]}
                        for item in menu.get("submenu", [])
                    ],
                }
                MENUS.append(MENU)
            ALL_MENUS[request.session.session_key] = MENUS
            return

        for app in base_dir_apps:
            if apps.is_installed(app):
                try:
                    sidebar = importlib.import_module(app + ".sidebar")

                except Exception as e:
                    logger.error(e)
                    continue

                if sidebar:
                    accessibility = None
                    if getattr(sidebar, "ACCESSIBILITY", None):
                        accessibility = import_method(sidebar.ACCESSIBILITY)

                    if not accessibility or accessibility(
                        request,
                        sidebar.MENU,
                        PermWrapper(request.user),
                    ):
                        MENU = {}
                        MENU["menu"] = sidebar.MENU
                        MENU["app"] = app
                        MENU["img_src"] = sidebar.IMG_SRC
                        MENU["submenu"] = []
                        MENUS.append(MENU)
                        for submenu in sidebar.SUBMENUS:

                            accessibility = None

                            if submenu.get("accessibility"):
                                accessibility = import_method(submenu["accessibility"])
                            redirect: str = submenu["redirect"]
                            redirect = redirect.split("?")
                            submenu["redirect"] = redirect[0]

                            if not accessibility or accessibility(
                                request,
                                submenu,
                                PermWrapper(request.user),
                            ):
                                MENU["submenu"].append(submenu)
        ALL_MENUS[request.session.session_key] = MENUS


def get_MENUS(request):
    ALL_MENUS[request.session.session_key] = []
    sidebar(request)
    return {"sidebar": ALL_MENUS.get(request.session.session_key)}
