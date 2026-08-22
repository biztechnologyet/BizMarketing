"""Bismillah — durable runtime patches for EthioBiz (ANFRG-26-00063).

Loaded from bizmarketing/hooks.py so these patches ship with the app via
Git and re-apply on every deploy / fresh server without editing frappe
core. Alhamdulillah.
"""

import frappe
from frappe import _


def _get_module_app_with_db_fallback(module):
    """ANFRG-26-00063 follow-up: poisoned/stale GLOBAL module-map caches
    (app_modules / installed_app_modules / all_apps in redis) made valid
    modules vanish mid-boot ("Module Healthcare not found"), which broke
    ALL Company creation & trial provisioning on prod.

    Strategy: try the stock resolver first; if the module is missing from
    the cached map, fall back to the authoritative Module Def record and
    heal the in-memory map before re-raising the original error only when
    the database agrees the module truly does not exist.
    """
    try:
        return frappe.modules.utils._ethiobiz_orig_get_module_app(module)
    except frappe.DoesNotExistError:
        pass

    app = None
    try:
        app = (
            frappe.db.get_value("Module Def", frappe.scrub(module), "app_name")
            or frappe.db.get_value(
                "Module Def", {"module_name": module}, "app_name")
        )
        if app:
            frappe.local.module_app[frappe.scrub(module)] = app
            frappe.logger("bizmarketing").info(
                "Alhamdulillah — monkeypatch healed module map for: %s -> %s"
                % (module, app))
    except Exception:
        app = None

    if not app:
        raise frappe.DoesNotExistError(
            _("Module {} not found").format(module))
    return app


def apply():
    """Idempotent install of all EthioBiz runtime patches."""
    import frappe.modules.utils

    utils = frappe.modules.utils
    if not hasattr(utils, "_ethiobiz_orig_get_module_app"):
        utils._ethiobiz_orig_get_module_app = utils.get_module_app
    utils.get_module_app = _get_module_app_with_db_fallback
