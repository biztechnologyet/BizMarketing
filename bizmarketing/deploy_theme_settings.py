"""One-shot deployer: EthioBiz Theme animation settings (Task C).

Idempotent Custom Field creation on the "EthioBiz Theme" Single DocType.
Run via runner pattern:
    from bizmarketing.deploy_theme_settings import execute; execute()
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


FIELDS = [
    dict(
        fieldname="enable_website_animation",
        label="Enable Website Animation",
        fieldtype="Check",
        default="1",
        insert_after="hide_sidebar",
        description=(
            "Site-wide animated constellation background on ethiobiz.et "
            "(website pages)."
        ),
    ),
    dict(
        fieldname="website_animation_speed",
        label="Website Animation Speed",
        fieldtype="Select",
        options="Slow\nNormal\nFast",
        default="Normal",
        insert_after="enable_website_animation",
        description="Baseline Normal runs at 0.7x of the original home-page speed.",
    ),
]


def execute():
    create_custom_fields(
        {"EthioBiz Theme": FIELDS}, ignore_validate=True, update=True
    )
    frappe.db.commit()
    print("THEME_SETTINGS_FIELDS_DEPLOYED")
