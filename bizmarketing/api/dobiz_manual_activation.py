import frappe
from frappe import _
from frappe.utils import now_datetime, today, add_days, get_datetime, getdate

# ============================================================
# DOBiz MANUAL ACTIVATION CORE (Bismillah)
# No account may be activated automatically after a bank
# transfer claim. An administrator must verify funds received
# in the bank account before enabling any user.
# Server Scripts are DISABLED on this instance: this module is
# the single server-side authority replacing the old
# client-script frappe.client.set_value chains.
# ============================================================

DOCTYPE = "DOBiz Payment Transaction"
ADMIN_ROLES = ("System Manager",)


def _is_admin():
    if frappe.session.user == "Administrator":
        return True
    return bool(set(ADMIN_ROLES).intersection(frappe.get_roles()))


def _settings_flag(flagname, default):
    try:
        val = frappe.db.get_single_value("DOBiz SaaS Settings", flagname)
        return default if val is None else bool(int(val))
    except Exception:
        return default


def manual_review_required():
    """When True, bank-transfer claims NEVER self-activate."""
    return _settings_flag("require_manual_bank_review", 1)


def online_auto_activation_enabled():
    """AddiPay webhook may auto-activate only when explicitly allowed."""
    return _settings_flag("auto_activate_online_payments", 1)


def _expected_amount(payment):
    """Sanity floor: one month of the linked subscription plan rate (if known)."""
    try:
        sub_name = getattr(payment, "subscription", None)
        if not sub_name or not frappe.db.exists("Subscription", sub_name):
            return 0.0
        sub = frappe.get_doc("Subscription", sub_name)
        if not sub.plans:
            return 0.0
        rate = frappe.db.get_value("Subscription Plan", sub.plans[0].plan, "rate")
        return float(rate or 0)
    except Exception:
        return 0.0


def _signup_from_payment(payment):
    if payment.linked_signup and frappe.db.exists("DOBiz Trial Signup", payment.linked_signup):
        return frappe.get_doc("DOBiz Trial Signup", payment.linked_signup)
    if payment.email:
        name = frappe.db.get_value("DOBiz Trial Signup", {"email": payment.email}, "name")
        if name:
            return frappe.get_doc("DOBiz Trial Signup", name)
    sub_name = getattr(payment, "subscription", None)
    if sub_name and frappe.db.exists("Subscription", sub_name):
        party = frappe.db.get_value("Subscription", sub_name, "party")
        name = frappe.db.get_value("DOBiz Trial Signup", {"company_name": party}, "name")
        if name:
            return frappe.get_doc("DOBiz Trial Signup", name)
    return None


def _activation_emails(user_email, full_name, plan_name):
    """First-time activation sends password setup; reactivation sends notice."""
    from bizmarketing.api.subscription_notifications import send_conversion_email

    last_login = frappe.db.get_value("User", user_email, "last_login")
    if not last_login:
        try:
            user = frappe.get_doc("User", user_email)
            password_link = user.reset_password(send_email=False)
            from bizmarketing.api.subscription_notifications import send_welcome_email
            send_welcome_email(
                user_email, full_name or user.first_name,
                frappe.db.get_value("User", user_email, "custom_company") or "",
                password_setup_link=password_link,
            )
            return
        except Exception as e:
            frappe.logger("bizmarketing").warning(f"Password-setup email fallback: {e}")
    try:
        send_conversion_email(user_email, full_name, plan_name)
    except Exception as e:
        frappe.logger("bizmarketing").warning(f"Conversion email failed: {e}")


def activate_account(signup_name, payment_doc=None, actor=None):
    """THE ONLY sanctioned path to enable a DOBiz customer account."""
    signup = frappe.get_doc("DOBiz Trial Signup", signup_name)
    result = {"user_enabled": False, "subscription_active": False}

    if signup.user_linked and frappe.db.exists("User", signup.user_linked):
        user = frappe.get_doc("User", signup.user_linked)
        if not user.enabled:
            user.enabled = 1
            user.flags.ignore_permissions = True
            user.save(ignore_permissions=True)
            result["user_enabled"] = True

    if signup.subscription_link and frappe.db.exists("Subscription", signup.subscription_link):
        sub = frappe.get_doc("Subscription", signup.subscription_link)
        end_date = sub.current_invoice_end
        # getdate() on both sides: today() yields a string while
        # current_invoice_end is a date — mixing them raises TypeError.
        if not end_date or getdate(end_date) < getdate(today()):
            sub.current_invoice_end = add_days(today(), 30)
        sub.db_set("status", "Active")
        result["subscription_active"] = True
        plan_name = sub.plans[0].plan if sub.plans else "DOBiz Standard Plan"

    signup.db_set("status", "Converted")

    if payment_doc is not None:
        payment_doc.db_set("payment_status", "Approved")
        payment_doc.db_set("approved_by", actor or frappe.session.user)
        payment_doc.db_set("approved_on", now_datetime())
        payment_doc.add_comment("Edit",
            f"Approved via manual bank verification by {actor or frappe.session.user}")

    _activation_emails(signup.email, signup.full_name,
        locals().get("plan_name", "DOBiz Standard Plan"))
    frappe.logger("bizmarketing").info(
        f"Bismillah. Account ACTIVATED manually for {signup.email} by {actor or frappe.session.user}")
    return result


@frappe.whitelist()
def get_pending_review_queue():
    """Admin queue: every bank-transfer claim awaiting verification."""
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    rows = frappe.get_all(
        DOCTYPE,
        filters={"payment_status": "Pending"},
        fields=["name", "customer", "email", "paid_by", "bank_name", "reference_no",
                "amount", "status", "payment_date", "creation", "linked_signup", "subscription"],
        order_by="creation asc",
    )
    queue = []
    for r in rows:
        expected = _expected_amount(r)
        queue.append({
            **r,
            "expected_amount": expected,
            "amount_ok": (not expected) or (float(r.amount or 0) >= expected),
        })
    return queue


@frappe.whitelist()
def approve_bank_payment(payment_name, confirmed=None, override_reason=None):
    """Approve AFTER funds verified in bank. confirmed must be truthy."""
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not confirmed:
        frappe.throw(_("You must confirm the funds are received in our bank account."))

    payment = frappe.get_doc(DOCTYPE, payment_name)
    if getattr(payment, "payment_status", "") == "Approved":
        return {"status": "already_approved", "message": _("Payment was already approved.")}
    if getattr(payment, "payment_status", "") == "Rejected":
        frappe.throw(_("This payment was rejected and cannot be approved."))

    expected = _expected_amount(payment)
    paid = float(payment.amount or 0)
    if expected and paid < expected:
        if not (override_reason and str(override_reason).strip()):
            frappe.throw(_(
                f"Paid amount {paid} is below the expected {expected}. "
                "Provide an override reason to approve anyway."))

    signup = _signup_from_payment(payment)
    if not signup:
        frappe.throw(_("Linked signup not found for this payment."))

    actor = frappe.session.user
    result = activate_account(signup.name, payment_doc=payment, actor=actor)

    if override_reason and str(override_reason).strip():
        payment.db_set("admin_remarks",
            f"{payment.admin_remarks or ''}\nOverride by {actor}: {override_reason}".strip())

    frappe.db.commit()
    return {
        "status": "success",
        "message": _("Funds verified. Account activated InSha'Allah."),
        **result,
    }


@frappe.whitelist()
def reject_bank_payment(payment_name, reason=None):
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not reason or not str(reason).strip():
        frappe.throw(_("A rejection reason is required."))

    payment = frappe.get_doc(DOCTYPE, payment_name)
    if getattr(payment, "payment_status", "") == "Approved":
        frappe.throw(_("Approved payments cannot be rejected."))

    payment.payment_status = "Rejected"
    payment.admin_remarks = f"{payment.admin_remarks or ''}\n{reason}".strip()
    payment.approved_by = frappe.session.user
    payment.approved_on = now_datetime()
    payment.db_set("payment_status", "Rejected")
    payment.add_comment("Edit", f"Rejected by {frappe.session.user}: {reason}")

    signup = _signup_from_payment(payment)
    if signup:
        signup.db_set("status", "Pending")
        try:
            _send_rejection_email(signup.email, signup.full_name, reason)
        except Exception as e:
            frappe.logger("bizmarketing").warning(f"Rejection email failed: {e}")

    frappe.db.commit()
    return {"status": "rejected", "message": _("Payment rejected and applicant notified.")}


@frappe.whitelist()
def activate_trial_account(signup_name):
    """Admin manually activates/vets a TRIAL account (login enabled)."""
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not frappe.db.exists("DOBiz Trial Signup", signup_name):
        frappe.throw(_("Signup not found"))
    result = activate_account(signup_name)
    frappe.db.commit()
    return {"status": "success", "message": _("Trial account activated InSha'Allah."), **result}


def _send_rejection_email(email, full_name, reason):
    _send_email(
        email,
        "Your DOBiz Payment Could Not Be Verified — Biz Technology Solutions",
        f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:linear-gradient(135deg,#b91c1c,#7f1d1d);padding:24px;border-radius:12px 12px 0 0;text-align:center;">
                <h1 style="color:white;margin:0;font-size:20px;">Payment Not Verified</h1>
            </div>
            <div style="background:#ffffff;padding:28px;border:1px solid #e0e0e0;">
                <p>Assalamu Alaikum <strong>{full_name or ''}</strong>,</p>
                <p>Unfortunately we could not verify your bank transfer for your DOBiz subscription.</p>
                <p><strong>Reason:</strong> {frappe.utils.escape_html(reason)}</p>
                <p>Please double-check the transfer reference and reply to this email, or register the
                payment again at <a href="{frappe.utils.get_url()}/dobiz-payment">ethiobiz.et/dobiz-payment</a>.</p>
            </div>
            <div style="background:#f5f5f5;padding:14px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#999;">
                <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
            </div>
        </div>""",
    )


def _send_email(email, subject, message):
    try:
        frappe.sendmail(recipients=[email], subject=subject, message=message, now=True)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send email to {email}: {e}")
