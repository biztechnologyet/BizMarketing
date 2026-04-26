"""
BISMALLAH — Subscription Cron Engine
Daily scheduled tasks for trial expiration, warnings, and status sync.

Registered in hooks.py scheduler_events["daily"].
"""
import frappe
from frappe.utils import today, add_days, getdate, date_diff
from bizmarketing.api.subscription_notifications import (
    send_welcome_email,
    send_expiry_warning_email,
    send_expired_email,
)


def check_trial_expirations():
    """
    Daily job: Find subscriptions with expired trial periods and process them.
    Frappe's native Subscription may not auto-transition status,
    so we enforce it here.
    """
    frappe.logger("bizmarketing").info("Bismillah. Checking trial expirations...")

    expired_subs = frappe.db.sql("""
        SELECT name, party, trial_period_start, trial_period_end, status
        FROM `tabSubscription`
        WHERE company = 'Biz Technology Solutions'
          AND trial_period_end IS NOT NULL
          AND trial_period_end < %s
          AND status IN ('Trialing', 'Active')
    """, (today(),), as_dict=True)

    for sub in expired_subs:
        try:
            doc = frappe.get_doc("Subscription", sub.name)
            # Cancel the subscription to trigger process_subscription_access
            doc.db_set("status", "Cancelled")
            frappe.logger("bizmarketing").info(
                f"Expired trial subscription {sub.name} for {sub.party}"
            )

            # Send expiry notification
            _notify_trial_expired(sub.party)

        except Exception as e:
            frappe.logger("bizmarketing").error(
                f"Error expiring subscription {sub.name}: {e}"
            )

    frappe.db.commit()
    frappe.logger("bizmarketing").info(
        f"Processed {len(expired_subs)} expired trial(s)."
    )


def send_expiry_warnings():
    """
    Daily job: Send warning emails for trials expiring in 3 days and 1 day.
    """
    frappe.logger("bizmarketing").info("Checking for upcoming trial expirations...")

    for days_ahead in [3, 1]:
        target_date = add_days(today(), days_ahead)
        expiring_subs = frappe.db.sql("""
            SELECT name, party, trial_period_end
            FROM `tabSubscription`
            WHERE company = 'Biz Technology Solutions'
              AND trial_period_end = %s
              AND status IN ('Trialing', 'Active')
        """, (target_date,), as_dict=True)

        for sub in expiring_subs:
            try:
                _notify_trial_expiring(sub.party, days_ahead, sub.trial_period_end)
                frappe.logger("bizmarketing").info(
                    f"Sent {days_ahead}-day warning for {sub.party}"
                )
            except Exception as e:
                frappe.logger("bizmarketing").error(
                    f"Error sending warning for {sub.party}: {e}"
                )

    frappe.db.commit()


def sync_trial_signup_status():
    """
    Daily job: Sync DOBiz Trial Signup status with its linked Subscription status.
    """
    frappe.logger("bizmarketing").info("Syncing Trial Signup statuses...")

    trial_signups = frappe.get_all(
        "DOBiz Trial Signup",
        filters={"status": ["in", ["Pending", "Trial Active"]]},
        fields=["name", "company_name", "email", "status"]
    )

    for signup in trial_signups:
        try:
            # Find the linked subscription via Customer name
            sub = frappe.db.get_value(
                "Subscription",
                {"party": signup.company_name, "company": "Biz Technology Solutions"},
                ["name", "status"],
                as_dict=True
            )

            if not sub:
                continue

            new_status = signup.status
            if sub.status in ["Active", "Trialing"]:
                new_status = "Trial Active"
            elif sub.status in ["Cancelled", "Past Due Date", "Unpaid"]:
                new_status = "Expired"

            if new_status != signup.status:
                frappe.db.set_value(
                    "DOBiz Trial Signup", signup.name, "status", new_status
                )
                frappe.logger("bizmarketing").info(
                    f"Synced {signup.name}: {signup.status} → {new_status}"
                )

        except Exception as e:
            frappe.logger("bizmarketing").error(
                f"Error syncing signup {signup.name}: {e}"
            )

    frappe.db.commit()


# ── Internal Helpers ────────────────────────────────────────────────

def _get_trial_email(customer_name):
    """Look up the email from the DOBiz Trial Signup linked to this customer."""
    email = frappe.db.get_value(
        "DOBiz Trial Signup",
        {"company_name": customer_name},
        "email"
    )
    return email


def _notify_trial_expiring(customer_name, days_remaining, expiry_date):
    """Send a trial expiry warning email."""
    email = _get_trial_email(customer_name)
    if email:
        send_expiry_warning_email(email, customer_name, days_remaining, expiry_date)


def _notify_trial_expired(customer_name):
    """Send a trial expired email."""
    email = _get_trial_email(customer_name)
    if email:
        send_expired_email(email, customer_name)
