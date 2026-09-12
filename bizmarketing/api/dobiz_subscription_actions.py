# Bismillah - DOBiz subscription ACTIONS: self-serve trial, renew, package
# upgrade, and the single admin approve/dispatch authority for these actions.
# First-time purchases keep using dobiz_signup_api.submit_dobiz_signup +
# dobiz_manual_activation.activate_account (untouched); this module adds the
# lifecycle actions the PRD requires (subscribe -> renew -> pay -> upgrade).
import frappe
from frappe import _
from frappe.utils import today, add_months, getdate

from bizmarketing.api import dobiz_signup_config as _cfg


def _log(msg):
    frappe.logger("bizmarketing").info(f"[dobiz_actions] {msg}")


def get_signup(signup_name):
    if not signup_name or not frappe.db.exists("DOBiz Trial Signup", signup_name):
        frappe.throw(_("Signup not found: {0}").format(signup_name),
                     exc=frappe.ValidationError)
    return frappe.get_doc("DOBiz Trial Signup", signup_name)


def resolve_package(industry, tier):
    """Full package metadata (max_users, module/role profiles) from the dynamic
    table rows (industry-scoped or global), falling back to built-ins."""
    settings = _cfg.get_signup_settings()
    ind = (industry or "").strip()
    for r in _cfg.get_package_items(settings, ind):
        if r.get("package_tier") == tier:
            r = dict(r)
            r["max_users"] = int(r.get("max_users") or 0) or 0
            return r
    return {"max_users": 0, "module_profile": None, "role_profile": None,
            "item_code": None, "features": []}


def _norm_bank_short(bank_name):
    if not bank_name:
        return "Other"
    b = str(bank_name).strip()
    low = b.lower()
    for key, opt in {"cbe": "CBE", "commercial": "CBE", "awash": "Awash",
                     "dashen": "Dashen", "birhan": "Birhan", "abyssinia": "Abyssinia",
                     "zemen": "Zemen", "oromia": "Oromia", "united": "United",
                     "telebirr": "Telebirr", "chapa": "Chapa"}.items():
        if key in low:
            return opt
    return b if b in ["CBE", "Dashen", "Birhan", "Awash", "Abyssinia", "Zemen",
                      "Oromia", "United", "Telebirr", "Chapa", "Other"] else "Other"


def _compute_amount(tier, months, coupon_code=None, industry=None):
    """Reuse the single money engine: rate -> term discount -> coupon."""
    settings = _cfg.get_signup_settings()
    months = int(_cfg.resolve_term(int(months or 0), settings)["months"])
    base = _cfg.get_live_monthly_rate(tier, settings, industry)
    row = _cfg.resolve_term(months, settings)
    pct = float(row["pct"]) / 100.0
    subtotal = round(base * months, 2)
    discount = round(subtotal * pct, 2)
    amount = round(max(0, subtotal - discount), 2)
    coupon_display = None
    if coupon_code:
        from bizmarketing.api import dobiz_coupon_api as _coupon
        ev = _coupon.evaluate(coupon_code, tier, months, amount)
        if not ev["valid"]:
            frappe.throw(_("Coupon error: {0}").format(ev["message"]),
                         exc=frappe.ValidationError)
        amount = round(max(0, amount - ev["discount_amount"]), 2)
        coupon_display = str(coupon_code).strip().upper()
        _coupon.consume(ev["coupon_name"])
    return {"tier": tier, "months": months, "base_monthly": base,
            "discount_percent": round(pct * 100, 2), "discount": discount,
            "total": amount, "coupon": coupon_display}


def _subscription_for(company):
    return frappe.db.get_value("Subscription", {"party": company}, "name")


def _plan_for_tier(tier):
    if tier and frappe.db.exists("Subscription Plan", tier):
        return tier
    trial = frappe.get_all("DOBiz SaaS Plan",
                           filters={"is_trial_plan": 1, "enabled": 1}, limit=1,
                           pluck="linked_erpnext_plan")
    if trial and trial[0] and frappe.db.exists("Subscription Plan", trial[0]):
        return trial[0]
    return frappe.db.get_value("Subscription Plan", {"disabled": 0}, "name")


def _create_action_txn(signup, sub_name, action, amount_row, payment_method,
                       payment_ref=None, bank_name=None):
    txn = frappe.get_doc({
        "doctype": "DOBiz Payment Transaction",
        "subscription": sub_name,
        "customer": signup.company_name,
        "email": signup.email,
        "paid_by": signup.full_name or signup.email,
        "bank_name": _norm_bank_short(bank_name),
        "reference_no": payment_ref or "",
        "amount": amount_row["total"],
        "status": "Pending",
        "payment_status": "Pending",
        "payment_date": today(),
        "linked_signup": signup.name,
        "custom_action": action,
        "custom_renewal_months": amount_row["months"],
        "custom_final_amount": amount_row["total"],
        "notes": f"{action} | {amount_row['tier']} | {amount_row['months']}mo "
                 f"| {amount_row['total']:,.2f} ETB"
                 + (f" | Coupon {amount_row['coupon']}" if amount_row["coupon"] else ""),
    })
    txn.insert(ignore_permissions=True)
    return txn


def _addipay_checkout(txn, signup, amount_row, package_tier, payment_method):
    """Create the AddisPay hosted order unless the amount is zero/bank-only."""
    if payment_method != "addipay" or amount_row["total"] <= 0:
        return None
    try:
        from bizmarketing.api.addispay import create_hosted_order, get_addispay_config
        cfg = get_addispay_config()
        if not cfg.get("api_key"):
            return None
        site = frappe.utils.get_url()
        ap_tx_ref = f"DOBIZ-{signup.name[-6:]}-{frappe.generate_hash(length=6)}"
        res = create_hosted_order(
            amount=amount_row["total"],
            tx_ref=ap_tx_ref,
            customer_email=signup.email,
            customer_name=signup.full_name or signup.email,
            phone_number=signup.phone,
            description=f"DOBiz {package_tier} - {signup.company_name} ({amount_row['months']}mo)",
            success_url=f"{site}/dobiz-payment?ref={signup.name}&status=success",
            error_url=f"{site}/dobiz-payment?ref={signup.name}&status=failed",
            message=f"DOBiz Smart ERP - {signup.company_name}",
        )
        uuid = res.get("uuid") or ap_tx_ref
        frappe.db.set_value("DOBiz Payment Transaction", txn.name,
                            {"addispay_transaction_id": uuid, "reference_no": ap_tx_ref})
        frappe.db.commit()
        return res.get("redirect") or res.get("checkout_url")
    except Exception as ae:
        _log(f"AddisPay initiation failed for {txn.name}: {ae}")
        return None


# --------------------------------------------------------------------------
# 1. SELF-SERVE FREE TRIAL  ->  https://ethiobiz.et/trial
# --------------------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def start_free_trial(full_name=None, email=None, phone=None, company_name=None,
                     industry=None, selected_module="Accounts"):
    """Zero human-step trial signup. The DOBiz Trial Signup after_insert hook
    (dobiz_trial.setup_trial_tenant) provisions the tenant, activates the owner
    user immediately and emails login credentials whenever self-serve is enabled
    in DOBiz SaaS Settings (allow_self_serve_trial)."""
    if not all([full_name, email, phone, company_name, industry]):
        frappe.throw(_("Full Name, Email, Phone, Company Name and Industry are required."),
                     exc=frappe.ValidationError)
    if not bool(frappe.db.get_single_value("DOBiz SaaS Settings", "allow_self_serve_trial")):
        frappe.throw(_("Free trial is temporarily unavailable. Please use the standard "
                       "registration form."), exc=frappe.ValidationError)

    email = email.strip().lower()
    if frappe.db.exists("User", email):
        frappe.throw(_("An account already exists for {0}").format(email),
                     exc=frappe.ValidationError)

    prev_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        signup = frappe.get_doc({
            "doctype": "DOBiz Trial Signup",
            "full_name": full_name.strip(),
            "email": email,
            "phone": phone.strip(),
            "company_name": company_name.strip(),
            "industry": (industry or "").strip(),
            "selected_module": selected_module or "Accounts",
            "subscription_type": "Trial",
            "status": "Pending",
        })
        signup.flags.ignore_permissions = True
        signup.insert(ignore_permissions=True)
        frappe.db.commit()
        sub_name = _subscription_for(signup.company_name)
        try:
            trial_days = frappe.db.get_single_value(
                "DOBiz SaaS Settings", "default_trial_duration_days")
        except Exception:
            trial_days = None
        return {
            "success": True,
            "message": "Your free trial is ready InSha'Allah! Login credentials are on their way.",
            "signup_ref": signup.name,
            "company": signup.company_name,
            "email": email,
            "subscription": sub_name,
            "trial_period_days": trial_days or 30,
        }
    finally:
        frappe.set_user(prev_user)


# --------------------------------------------------------------------------
# 2. RENEWAL
# --------------------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def renew_subscription(signup_name, billing_term="3", payment_method="bank_transfer",
                       payment_ref=None, bank_name=None, coupon_code=None):
    """Renew an existing tenant. Bank flows create a Pending transaction for the
    admin queue (approve_renewal/bank dispatch), online flows redirect to AddisPay."""
    signup = get_signup(signup_name or str(frappe.form_dict.get("signup_ref") or ""))
    sub_name = _subscription_for(signup.company_name)
    if not sub_name:
        frappe.throw(_("No active subscription found for {0}").format(signup.company_name),
                     exc=frappe.ValidationError)

    tier = signup.get("custom_package_tier") or "Business Growth"
    amount_row = _compute_amount(tier, billing_term, coupon_code, signup.industry)
    manual_review = _is_manual_review(amount_row["total"])

    txn = _create_action_txn(signup, sub_name, "Renew", amount_row, payment_method,
                             payment_ref, bank_name)
    checkout_url = _addipay_checkout(txn, signup, amount_row, tier, payment_method)
    frappe.db.commit()

    resp = {
        "success": True,
        "message": ("Renewal payment received; our team will verify your transfer "
                    "within 24 hours InSha'Allah." if manual_review
                    else "Renewal payment recorded successfully Alhamdulillah!"),
        "renewal_txn": txn.name,
        "payment_amount": amount_row["total"],
        "months": amount_row["months"],
        "pending_review": bool(manual_review),
        "package_tier": tier,
        "payment_method": "addipay" if checkout_url else "bank_transfer",
    }
    if checkout_url:
        resp["checkout_url"] = checkout_url
    if payment_ref:
        resp["payment_ref"] = payment_ref
    return resp


# --------------------------------------------------------------------------
# 3. PACKAGE UPGRADE
# --------------------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def upgrade_package(signup_name, package_tier, billing_term="3",
                    payment_method="bank_transfer", payment_ref=None,
                    bank_name=None, coupon_code=None):
    """Move a tenant to a higher package. The price difference and the new tier's
    max_users/module profile are applied only after payment is approved."""
    signup = get_signup(signup_name or str(frappe.form_dict.get("signup_ref") or ""))
    sub_name = _subscription_for(signup.company_name)
    if not sub_name:
        frappe.throw(_("No active subscription found for {0}").format(signup.company_name),
                     exc=frappe.ValidationError)

    current = signup.get("custom_package_tier") or "Business Growth"
    if current == package_tier:
        frappe.throw(_("Already on the {0} package").format(package_tier),
                     exc=frappe.ValidationError)
    pm = resolve_package(signup.industry, package_tier)
    if not pm.get("item_code") and package_tier not in _cfg.get_package_tiers():
        frappe.throw(_("Unknown package: {0}").format(package_tier),
                     exc=frappe.ValidationError)

    amount_row = _compute_amount(package_tier, billing_term, coupon_code, signup.industry)
    manual_review = _is_manual_review(amount_row["total"])

    txn = _create_action_txn(signup, sub_name, "Upgrade", amount_row, payment_method,
                             payment_ref, bank_name)
    frappe.db.set_value("DOBiz Payment Transaction", txn.name, {"custom_target_tier": package_tier})
    checkout_url = _addipay_checkout(txn, signup, amount_row, package_tier, payment_method)
    frappe.db.commit()

    resp = {
        "success": True,
        "message": ("Upgrade payment received; applied after verification InSha'Allah."
                    if manual_review else "Upgrade payment recorded Alhamdulillah!"),
        "upgrade_txn": txn.name,
        "from_package": current,
        "to_package": package_tier,
        "payment_amount": amount_row["total"],
        "months": amount_row["months"],
        "new_max_users": pm.get("max_users", 0),
        "pending_review": bool(manual_review),
        "payment_method": "addipay" if checkout_url else "bank_transfer",
    }
    if checkout_url:
        resp["checkout_url"] = checkout_url
    if payment_ref:
        resp["payment_ref"] = payment_ref
    return resp


def _is_manual_review(total_amount):
    try:
        from bizmarketing.api.dobiz_manual_activation import manual_review_required
        return bool(manual_review_required() and total_amount > 0)
    except Exception:
        return total_amount > 0


# --------------------------------------------------------------------------
# 4. ADMIN DISPATCH - single approve authority for the payment queue
# --------------------------------------------------------------------------
def dispatch_action(payment_doc, note=None):
    """Called after a payment is verified. Subscriptions keep activate_account;
    renews extend the period; upgrades swap package + limit + profiles."""
    action = str(payment_doc.get("custom_action") or "Subscribe").strip().title()
    if action not in ("Renew", "Upgrade"):
        from bizmarketing.api.dobiz_manual_activation import activate_account
        signup = _signup_of(payment_doc)
        return activate_account(signup.name, payment_doc=payment_doc,
                                actor=frappe.session.user)
    if action == "Renew":
        return _apply_renewal(payment_doc, note)
    return _apply_upgrade(payment_doc, note)


def _apply_renewal(payment_doc, note=None):
    sub_name = payment_doc.subscription
    months = int(payment_doc.get("custom_renewal_months") or 0) or 3
    signup = _signup_of(payment_doc)
    sub = frappe.get_doc("Subscription", sub_name)
    base = getdate(sub.current_invoice_end or today())
    if base < getdate(today()):
        base = today()
    sub.current_invoice_end = add_months(base, months)
    if sub.status == "Cancelled":
        sub.status = "Active"
    sub.flags.ignore_permissions = True
    sub.save(ignore_permissions=True)
    _mark_txn_approved(payment_doc, note)
    _notify(payment_doc, signup, months)
    return {"status": "renewed", "subscription": sub_name, "months": months,
            "new_end": str(sub.current_invoice_end)}


def _apply_upgrade(payment_doc, note=None):
    sub_name = payment_doc.subscription
    target = payment_doc.get("custom_target_tier")
    if not target:
        frappe.throw(_("Upgrade target tier missing on transaction."),
                     exc=frappe.ValidationError)
    signup = _signup_of(payment_doc)
    pm = resolve_package(signup.industry, target)

    sub = frappe.get_doc("Subscription", sub_name)
    new_plan = _plan_for_tier(target) or _plan_for_tier(signup.get("custom_package_tier"))
    current_plan = sub.plans[0].plan if sub.plans else None
    if current_plan:
        for row in list(sub.plans):
            sub.remove(row)
    if new_plan:
        sub.append("plans", {"plan": new_plan, "qty": 1})
    months = int(payment_doc.get("custom_renewal_months") or 0) or 3
    sub.current_invoice_start = today()
    sub.current_invoice_end = add_months(today(), months)
    sub.status = "Active"
    sub.flags.ignore_permissions = True
    sub.save(ignore_permissions=True)

    signup.custom_package_tier = target
    signup.custom_max_users = pm.get("max_users", 0)
    signup.custom_module_profile = (pm.get("module_profile")
                                    or signup.custom_module_profile)
    signup.status = "Converted"
    signup.flags.ignore_permissions = True
    signup.save(ignore_permissions=True)

    # Re-provision roles/modules on the owner user to match the new tier.
    _reprovision_owner(signup, target)
    _mark_txn_approved(payment_doc, note)
    _notify(payment_doc, signup, months, upgrade=target)
    return {"status": "upgraded", "subscription": sub_name, "plan": new_plan,
            "to_package": target, "max_users": pm.get("max_users", 0)}


def _reprovision_owner(signup, target):
    owner_email = signup.email
    if not frappe.db.exists("User", owner_email):
        return
    try:
        from bizmarketing.api.dobiz_signup_config import get_industry_role_profiles
        from bizmarketing.api.dobiz_signup_api import INDUSTRY_FULL_PROFILES
        module = signup.get("selected_module") or "Accounts"
        db_rp, db_mp = get_industry_role_profiles(signup.industry)
        if db_rp:
            role_profile, module_profile = db_rp, db_mp
        elif (target or "").lower().startswith("starter") or target == "Starter Module":
            role_profile = "DOBiz Starter User"
            module_profile = (f"DOBiz Starter - {module}"
                              if frappe.db.exists("Module Profile", f"DOBiz Starter - {module}")
                              else "DOBiz Starter - Accounts")
        elif "Growth" in (target or ""):
            role_profile = "DOBiz Growth Enterprise"
            module_profile = "DOBiz Growth - Standard"
        else:
            rp, mp = INDUSTRY_FULL_PROFILES.get(
                signup.industry, ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"))
            role_profile = rp if frappe.db.exists("Role Profile", rp) else "DOBiz Growth Enterprise"
            module_profile = mp if frappe.db.exists("Module Profile", mp) else "DOBiz Growth - Standard"
        user_doc = frappe.get_doc("User", owner_email)
        user_doc.role_profile_name = role_profile
        if module_profile:
            user_doc.module_profile = module_profile
        user_doc.flags.ignore_permissions = True
        user_doc.save(ignore_permissions=True)
    except Exception as e:
        _log(f"Owner profile reprovision skipped for {target}: {e}")


def _signup_of(payment_doc):
    name = payment_doc.get("linked_signup")
    if name and frappe.db.exists("DOBiz Trial Signup", name):
        return frappe.get_doc("DOBiz Trial Signup", name)
    company = payment_doc.get("customer")
    if company:
        name2 = frappe.db.get_value("DOBiz Trial Signup", {"company_name": company}, "name")
        if name2:
            return frappe.get_doc("DOBiz Trial Signup", name2)
    frappe.throw(_("Linked signup not found for this payment action."),
                 exc=frappe.ValidationError)


def _mark_txn_approved(payment_doc, note=None):
    payment_doc.status = "Completed"
    payment_doc.payment_status = "Approved"
    if note:
        payment_doc.notes = (payment_doc.notes or "") + " | " + note
    payment_doc.flags.ignore_permissions = True
    payment_doc.save(ignore_permissions=True)


def _notify(payment_doc, signup, months, upgrade=None):
    try:
        subject = (f"DOBiz Package Upgrade Confirmed - {signup.company_name} -> {upgrade}"
                   if upgrade else f"DOBiz Renewal Confirmed - {signup.company_name}")
        message = (f"Dear {signup.full_name}, your DOBiz package upgrade to <b>{upgrade}</b> "
                   f"is complete. Your subscription now covers {months} months."
                   if upgrade else
                   f"Dear {signup.full_name}, your DOBiz subscription has been renewed for "
                   f"{months} more months.")
        frappe.sendmail(recipients=[signup.email], subject=subject, message=message,
                        delayed=True)
    except Exception as e:
        _log(f"action receipt email skipped: {e}")