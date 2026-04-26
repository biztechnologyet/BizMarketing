"""
BISMALLAH — Subscription Webhooks
Triggers events to BizFlow (n8n) for trial and subscription lifecycle events.
"""
import frappe
import requests
import json

def fire_subscription_event(event_type, payload):
    """
    Fire a generic event to the BizFlow webhook.
    Events: 'trial_started', 'trial_expiring_soon', 'trial_expired', 'subscription_upgraded'
    """
    try:
        # Retrieve the webhook URL from HADEEDA Company Settings (acting as the central webhook hub)
        # Or fall back to a specific bizflow endpoint if settings aren't available
        webhook_url = frappe.db.get_single_value("HADEEDA Company Settings", "webhook_url")
        if not webhook_url:
            frappe.logger("bizmarketing").warning("BizFlow Webhook URL not configured. Skipping webhook.")
            return

        headers = {
            "Content-Type": "application/json",
            "X-EthioBiz-Event": event_type
        }

        # Enhance payload with event type
        data = payload.copy()
        data["event_type"] = event_type

        # Fire and forget via background job, or synchronous if fast enough
        response = requests.post(webhook_url, json=data, headers=headers, timeout=5)
        
        if response.status_code in [200, 201, 202, 204]:
            frappe.logger("bizmarketing").info(f"Fired {event_type} webhook to BizFlow successfully.")
        else:
            frappe.logger("bizmarketing").error(f"BizFlow webhook failed: {response.status_code} - {response.text}")

    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error firing BizFlow webhook: {e}")

def notify_trial_started(doc):
    """Called from dobiz_trial.setup_trial_tenant"""
    payload = {
        "company_name": doc.company_name,
        "email": doc.email,
        "full_name": doc.full_name,
        "phone": doc.phone,
        "industry": doc.industry,
        "status": doc.status
    }
    frappe.enqueue(
        "bizmarketing.api.subscription_webhooks.fire_subscription_event",
        event_type="trial_started",
        payload=payload,
        queue="short"
    )

def notify_subscription_upgraded(subscription_name, plan_name, customer_name):
    """Called from subscription_upgrade.upgrade_subscription"""
    payload = {
        "subscription": subscription_name,
        "plan_name": plan_name,
        "customer": customer_name
    }
    frappe.enqueue(
        "bizmarketing.api.subscription_webhooks.fire_subscription_event",
        event_type="subscription_upgraded",
        payload=payload,
        queue="short"
    )
