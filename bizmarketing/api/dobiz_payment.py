import frappe
from frappe.utils import now_datetime, get_url

# ============================================================
# DOBiz Payment System - Dual Mode (Direct Bank + AddiPay)
# ============================================================
# IMPORTANT: Server Scripts are DISABLED on this instance.
# Approval logic is handled CLIENT-SIDE via the Client Script
# on DOBiz Payment Transaction, which calls frappe.client.set_value
# via the REST API to activate accounts.
# ============================================================

DOCTYPE = "DOBiz Payment Transaction"

VALID_BANKS = [
    "CBE", "Dashen", "Birhan", "Awash", "Abyssinia",
    "Zemen", "Oromia", "United", "Telebirr", "Chapa", "Other"
]

BANK_DETAILS = {
    "bank": "Commercial Bank of Ethiopia (CBE)",
    "account_name": "Biz Technology Solutions",
    "account_no": "1000134567890",
    "swift_code": "CBETETAA"
}

PAYMENT_URL = get_url() + "/dobiz-payment"


def _send_email(email, subject, message):
    try:
        frappe.sendmail(
            recipients=[email],
            sender="onboard@ethiobiz.et",
            display_sender="DOBiz by EthioBiz <onboard@ethiobiz.et>",
            subject=subject,
            message=message,
            now=True,
        )
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send email to {email}: {e}")


def _get_settings():
    try:
        return frappe.get_cached_doc("DOBiz SaaS Settings")
    except Exception:
        return frappe.get_single("DOBiz SaaS Settings")


def _check_payment_mode():
    settings = _get_settings()
    mode = getattr(settings, "payment_mode", "Both") or "Both"
    if mode == "Direct Bank Only":
        return "direct"
    elif mode == "AddiPay Only":
        return "addipay"
    return "both"


# ── REFERENCE: register_payment (for future deployment) ──
# When dobiz_payment.py is deployed via git/bench, this function
# handles direct bank payment registration. Currently the web form
# creates DOBiz Payment Transaction records directly, and the Client
# Script handles approval via frappe.client.set_value API calls.
# ──────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def register_payment(email, paid_by, bank_name, reference_no, paid_amount, company_name=None, payment_request=None):
    bank_name = bank_name.strip()
    if bank_name not in VALID_BANKS:
        frappe.throw(f"Invalid bank. Must be one of: {', '.join(VALID_BANKS)}")

    signup = frappe.db.get_value(
        "DOBiz Trial Signup",
        {"email": email},
        ["name", "full_name", "company_name", "subscription_link", "user_linked"],
        as_dict=True
    )
    if not signup:
        frappe.throw("No trial signup found for this email")

    paymode = _check_payment_mode()
    if paymode == "addipay":
        frappe.throw("Direct bank payment is disabled. Please use the online payment option.")

    pr_name = payment_request or ""
    if pr_name and not frappe.db.exists("Payment Request", pr_name):
        frappe.throw(f"Payment Request {pr_name} not found")

    payment = frappe.get_doc({
        "doctype": DOCTYPE,
        "customer": company_name or signup.company_name,
        "email": email,
        "paid_by": paid_by,
        "bank_name": bank_name,
        "reference_no": reference_no,
        "amount": frappe.utils.flt(paid_amount),
        "payment_date": now_datetime(),
        "payment_status": "Pending",
        "payment_request": pr_name,
        "subscription": signup.subscription_link or "",
        "linked_signup": signup.name,
        "status": "Pending"
    })
    payment.insert(ignore_permissions=True)

    if pr_name:
        try:
            pr_doc = frappe.get_doc("Payment Request", pr_name)
            pr_doc.db_set("status", "Payment Initiated")
        except Exception:
            pass

    frappe.db.commit()
    return {
        "status": "success",
        "message": "Your payment registration has been received. We will activate your account within 24 hours InSha'Allah."
    }


# ── REFERENCE: approve_payment (for future deployment) ──
# Currently handled by the Client Script which calls:
#   frappe.client.set_value
#   frappe.client.get_value
#   frappe.client.get
# via the REST API to activate the account.
# ─────────────────────────────────────────────────────

@frappe.whitelist()
def approve_payment(payment_name):
    payment = frappe.get_doc(DOCTYPE, payment_name)
    pst = getattr(payment, "payment_status", payment.status)
    if pst in ("Approved", "Completed"):
        frappe.throw("Payment already processed")

    payment.payment_status = "Approved"
    payment.approved_by = frappe.session.user
    payment.approved_on = now_datetime()
    payment.save(ignore_permissions=True)

    if payment.linked_signup:
        signup = frappe.get_doc("DOBiz Trial Signup", payment.linked_signup)
        if signup.user_linked:
            frappe.db.set_value("User", signup.user_linked, "enabled", 1)
        if signup.subscription_link:
            from frappe.utils import add_days
            sub = frappe.get_doc("Subscription", signup.subscription_link)
            sub.db_set("status", "Active")
            sub.db_set("current_invoice_end", add_days(now_datetime().date(), 30))
        signup.db_set("status", "Converted")
        plan_name = "DOBiz Standard"
        if signup.subscription_link:
            sub_doc = frappe.get_doc("Subscription", signup.subscription_link)
            if sub_doc.plans:
                plan_name = sub_doc.plans[0].plan
        try:
            from bizmarketing.api.subscription_notifications import send_conversion_email
            send_conversion_email(signup.email, signup.full_name, plan_name)
        except Exception:
            pass

    frappe.db.commit()
    return {"status": "success", "message": "Payment approved, account activated InSha'Allah"}


# ── EMAIL FUNCTIONS ──

def send_payment_invite_email(email, full_name, company_name, days_remaining, expiry_date):
    """Send payment invite with both Pay Online (AddiPay) and Pay via Bank options."""
    settings = _get_settings()
    mode = getattr(settings, "payment_mode", "Both") or "Both"

    context = {
        "full_name": full_name,
        "company_name": company_name,
        "days_remaining": days_remaining,
        "expiry_date": expiry_date,
        "payment_url": f"{PAYMENT_URL}?email={email}&company={company_name}",
        "login_url": get_url() + "/app",
        "bank_name": BANK_DETAILS["bank"],
        "account_name": BANK_DETAILS["account_name"],
        "account_no": BANK_DETAILS["account_no"],
        "swift_code": BANK_DETAILS["swift_code"],
        "payment_mode": mode,
        "addispay_endpoint": get_url() + "/api/method/bizmarketing.api.addispay.handle_webhook"
    }
    subject = f"Complete Your Payment — DOBiz Trial Ending in {days_remaining} Day(s)"
    message_html = _payment_invite_html(context)
    _send_email(email, subject, message_html)
    frappe.logger("bizmarketing").info(f"Payment invite sent to {email} for {company_name}")


def send_payment_received_confirmation(email, full_name):
    subject = "Payment Registration Received — DOBiz Smart ERP"
    message = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#ff9800,#e65100);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:22px;">Payment Registered</h1>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Your payment registration has been received successfully.</p>
            <p>Our team will verify your payment and activate your DOBiz account within <strong>24 hours</strong> InSha'Allah.</p>
            <p>You will receive an email once your account is activated.</p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""
    _send_email(email, subject, message)


def _payment_invite_html(ctx):
    mode = ctx.get("payment_mode", "Both")
    online_section = ""
    bank_section = ""

    if mode != "Direct Bank Only":
        online_section = f"""
        <div style="background:#f0fdf4;border:2px solid #16a34a;border-radius:8px;padding:15px;margin:15px 0;">
            <h3 style="color:#166534;margin:0 0 8px 0;">Option 1: Pay Online (Instant)</h3>
            <p style="margin:5px 0;">Pay instantly via CBE Birr, Telebirr, or Cards</p>
            <a href="{ctx['login_url']}" style="background:#16a34a;color:white;padding:10px 25px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;">Pay Online Now</a>
        </div>"""

    if mode != "AddiPay Only":
        bank_section = f"""
        <div style="background:#fff8e1;border:2px solid #ff9800;border-radius:8px;padding:15px;margin:15px 0;">
            <h3 style="color:#e65100;margin:0 0 8px 0;">Option 2: Bank Transfer</h3>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:4px 8px;font-weight:bold;width:120px;">Bank</td>
                    <td style="padding:4px 8px;">{ctx['bank_name']}</td></tr>
                <tr><td style="padding:4px 8px;font-weight:bold;">Account</td>
                    <td style="padding:4px 8px;">{ctx['account_name']}</td></tr>
                <tr><td style="padding:4px 8px;font-weight:bold;">Account No</td>
                    <td style="padding:4px 8px;">{ctx['account_no']}</td></tr>
                <tr><td style="padding:4px 8px;font-weight:bold;">Swift</td>
                    <td style="padding:4px 8px;">{ctx['swift_code']}</td></tr>
            </table>
            <a href="{ctx['payment_url']}" style="background:#e65100;color:white;padding:10px 25px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:8px;">Register Bank Payment</a>
        </div>"""

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#ff9800,#e65100);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:22px;">Complete Your Payment</h1>
            <p style="color:#ffe0b2;margin-top:8px;">{ctx['days_remaining']} day(s) remaining in trial</p>
        </div>
        <div style="background:#ffffff;padding:30px;border:1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{ctx['full_name']}</strong>,</p>
            <p>Your DOBiz free trial for <strong>{ctx['company_name']}</strong> will expire on <strong>{ctx['expiry_date']}</strong>.</p>
            <p>To continue uninterrupted, please choose a payment option:</p>
            {online_section}
            {bank_section}
            <p style="text-align:center;font-size:12px;color:#999;margin-top:15px;">
                Once payment is complete, your account will be activated within 24 hours.
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>"""
