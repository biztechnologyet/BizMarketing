"""Public theme settings for EthioBiz (Bismillah).

Guest-safe, cache-friendly endpoint consumed by ethiobiz_theme.js (sidebar
behaviour) and ethiobiz_particles.js (site-wide animated background).
Values come from the "EthioBiz Theme" Single DocType; safe defaults apply
when the singleton has never been saved.
"""

import frappe


SPEED_FACTORS = {"Slow": 0.45, "Normal": 0.7, "Fast": 0.95}


def _flag(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() in ("1", "true", "True", "on", "yes")
    return bool(value)


@frappe.whitelist(allow_guest=True)
def public_theme_settings():
    try:
        hide_sidebar = frappe.db.get_single_value("EthioBiz Theme", "hide_sidebar")
        enable_anim = frappe.db.get_single_value(
            "EthioBiz Theme", "enable_website_animation"
        )
        speed = frappe.db.get_single_value(
            "EthioBiz Theme", "website_animation_speed"
        )
    except Exception:
        frappe.log_error(
            "theme_settings: failed reading EthioBiz Theme",
            "ethiobiz_theme_settings",
        )
        hide_sidebar = enable_anim = speed = None

    return {
        "hide_sidebar": _flag(hide_sidebar, True),
        "enable_website_animation": _flag(enable_anim, True),
        "animation_speed_factor": SPEED_FACTORS.get(speed, SPEED_FACTORS["Normal"]),
        "reduced_motion_respect": True,
    }
