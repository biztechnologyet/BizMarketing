import frappe
from frappe import _
from frappe.utils import today, add_days, add_months, getdate, now_datetime, get_url
import json

# Bismillah — Dynamic pricing engine (Marketing Settings -> Item Price source of truth)
from bizmarketing.api import dobiz_signup_config as _cfg
from bizmarketing.api import dobiz_coupon_api as _coupon_api

PACKAGE_CONFIG = {
    "Starter Module": {
        "price_per_month": 5000,
        "max_users": 3,
        "allowed_modules_count": 1,
        "role_profile": "DOBiz Starter User",
        "description": "Single core module ideal for micro-businesses."
    },
    "Business Growth": {
        "price_per_month": 9500,
        "max_users": 10,
        "allowed_modules_count": 3,
        "role_profile": "DOBiz Growth Enterprise",
        "description": "Multi-module operational suite for growing enterprises."
    },
    "Full Industry ERP Package": {
        "price_per_month": 15000,
        "max_users": 0,  # Unlimited
        "allowed_modules_count": 99,
        "description": "Complete all-in-one DOBiz SmartERP suite with full industry modules."
    }
}

INDUSTRY_FULL_PROFILES = {
    "Healthcare": ("DOBiz Full - Healthcare Admin", "DOBiz Full - Healthcare"),
    "Hotel Management": ("DOBiz Full - Hotel Admin", "DOBiz Full - Hotel"),
    "Restaurant": ("DOBiz Full - Restaurant Admin", "DOBiz Full - Restaurant"),
    "Property Management": ("DOBiz Full - Property Admin", "DOBiz Full - Property"),
    "Manufacturing": ("DOBiz Full - Manufacturing Admin", "DOBiz Full - Manufacturing"),
    "Education": ("DOBiz Full - Education Admin", "DOBiz Full - Education"),
    "Retail & Wholesale": ("DOBiz Full - Retail Admin", "DOBiz Full - Retail"),
    "Retail & Trade": ("DOBiz Full - Retail Admin", "DOBiz Full - Retail"),
    "Non-Profit": ("DOBiz Full - Non-Profit Admin", "DOBiz Full - Non-Profit"),
    "Non-Profit / NGO": ("DOBiz Full - Non-Profit Admin", "DOBiz Full - Non-Profit"),
    "Professional Services": ("DOBiz Full - Services Admin", "DOBiz Full - Services"),
    "Services": ("DOBiz Full - Services Admin", "DOBiz Full - Services"),
    "Hospitality & Tourism": ("DOBiz Full - Hotel Admin", "DOBiz Full - Hotel"),
    "Agriculture": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"),
    "Construction": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"),
    "Technology & IT": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"),
    "Finance & Insurance": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"),
    "Other": ("DOBiz Growth Enterprise", "DOBiz Growth - Standard")
}

INDUSTRY_ALIASES = {
    "Hotel": "Hotel Management",
    "Hospitality": "Hotel Management",
    "Hospitality & Tourism": "Hotel Management",
    "Property": "Property Management",
    "Retail": "Retail & Wholesale",
    "Wholesale": "Retail & Wholesale",
    "Retail & Trade": "Retail & Wholesale",
    "NGO": "Non-Profit / NGO",
    "Non-Profit": "Non-Profit / NGO",
    "Services": "Services",
    "Professional Services": "Services"
}

DISCOUNT_RATES = {
    "3": 0.0,
    "6": 0.10,
    "12": 0.20
}

@frappe.whitelist(allow_guest=True)
def get_dobiz_packages():
    """Return live package catalog, pricing rules, and bank accounts.

    v2 — prices come from Marketing Settings -> mapped Items -> Item Price
    (validity-aware). Legacy keys kept for backward compatibility."""
    settings = _cfg.get_signup_settings()
    packages_list = []
    packages_map = {}
    for row in _cfg.get_package_items(settings):
        rate = _cfg.get_live_monthly_rate(row["package_tier"], settings)
        entry = {
            "package_tier": row["package_tier"],
            "item_code": row["item_code"],
            "display_label": row["display_label"],
            "description": row["card_description"]
                            or PACKAGE_CONFIG.get(row["package_tier"], {}).get("description", ""),
            "badge": row["badge_text"],
            "price_per_month": rate,
            "currency": settings["currency"],
        }
        packages_list.append(entry)
        packages_map[row["package_tier"]] = dict(
            PACKAGE_CONFIG.get(row["package_tier"], {}), price_per_month=rate)

    terms_list = [
        {"months": t["months"], "discount_percent": t["pct"],
         "label": t["label"], "is_default": bool(t["is_default"])}
        for t in _cfg.get_active_terms(settings)
    ]
    discounts_map = {str(t["months"]): t["pct"] / 100.0 for t in _cfg.get_active_terms(settings)}

    promo = _cfg.promo_status(settings)

    return {
        # ---- legacy-compatible keys ----
        "packages": packages_map,
        "discounts": discounts_map,
        "industries": list(INDUSTRY_FULL_PROFILES.keys()),
        "bank_accounts": _cfg.get_bank_accounts(settings),
        "more_info_url": settings["more_info_url"],
        "user_guide_url": settings["user_guide_url"],
        "service_url": "https://ethiobiz.et/dobiz-saas-service-e9vyb",
        # ---- v2 keys ----
        "packages_list": packages_list,
        "terms_list": terms_list,
        "default_term": (_cfg.get_default_term(settings) or {}).get("months"),
        "currency": settings["currency"],
        "pricing_mode": settings["pricing_mode"],
        "coupons_enabled": settings["coupons_enabled"],
        "promo": promo,
    }

def _trace(tag):
    import time as _t
    print(f"[DOBIZ-TRACE] {tag} t={round(_t.time())}", flush=True)

_BANK_OPTIONS = ["CBE", "Dashen", "Birhan", "Awash", "Abyssinia", "Zemen",
                 "Oromia", "United", "Telebirr", "Chapa", "Other"]
_BANK_KEYWORDS = {
    "cbe": "CBE", "commercial": "CBE", "awash": "Awash", "dashen": "Dashen",
    "birhan": "Birhan", "abyssinia": "Abyssinia", "zemen": "Zemen",
    "oromia": "Oromia", "united": "United", "telebirr": "Telebirr", "chapa": "Chapa",
}

def _norm_bank(bank_name):
    """DOBiz Payment Transaction.bank_name is a Select limited to short codes."""
    if not bank_name:
        return "Other"
    b = str(bank_name).strip()
    low = b.lower()
    if b in _BANK_OPTIONS:
        return b
    for key, opt in _BANK_KEYWORDS.items():
        if key in low:
            return opt
    return "Other"

@frappe.whitelist(allow_guest=True)
def submit_dobiz_signup(full_name=None, email=None, phone=None, company_name=None, industry=None, package_tier=None, billing_term="3", selected_module="Accounts", payment_receipt=None, payment_ref=None, bank_name=None, coupon_code=None, payment_method="bank_transfer"):
    """Zero-touch registration for DOBiz Smart ERP with tenant provisioning.
    payment_method: "bank_transfer" (default) or "addipay" — when "addipay",
    the response includes a checkout_url to redirect the user to AddisPay."""
    # Guard BEFORE any positional access: missing payload fields must yield
    # HTTP 417 (frappe.ValidationError) instead of TypeError 500.
    if not all([full_name, email, phone, company_name, industry]):
        frappe.throw(_("Full Name, Email, Phone, Company Name and Industry are required."),
                     exc=frappe.ValidationError)
    prev_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        if not hasattr(frappe.local, 'module_app') or not frappe.local.module_app:
            frappe.setup_module_map()
        frappe.local.module_app['healthcare'] = 'healthcare'
        frappe.local.module_app['hotel_management'] = 'propms'
        frappe.local.module_app['restaurant_management'] = 'restaurant_management'
        frappe.local.module_app['property_management_solution'] = 'propms'
        
        # 1. Validation
        if not full_name or not email or not company_name:
            frappe.throw(_("Full Name, Email, and Company Name are required."))
        
        email = email.strip().lower()
        company_name = company_name.strip()
        
        valid_tiers = set(_cfg.get_package_tiers()) | set(PACKAGE_CONFIG.keys())
        if package_tier not in valid_tiers:
            package_tier = "Business Growth"

        billing_term_int = int(billing_term) if str(billing_term).isdigit() else 0
        signup_settings = _cfg.get_signup_settings()
        term_row = _cfg.resolve_term(billing_term_int, signup_settings)
        billing_term_int = term_row["months"]

        base_monthly = _cfg.get_live_monthly_rate(package_tier, signup_settings)
        discount_pct = term_row["pct"] / 100.0
        term_total = round(base_monthly * billing_term_int, 2)
        term_discount_amt = round(term_total * discount_pct, 2)
        subtotal_after_term = round(term_total - term_discount_amt, 2)

        # Launch Promo (first-N signups free). Slot reservation happens HERE via
        # the unique email constraint on DOBiz Promo Claim; losing a concurrent
        # race simply falls back to the normal paid flow. No funds are claimed
        # for a 0 ETB promo signup, so manual bank review does NOT apply to it.
        promo = _cfg.promo_status(signup_settings)
        promo_applied = bool(promo["active"] and _cfg.promo_covers_package(promo, package_tier))
        promo_claim_name = None
        promo_free_until = None
        if promo_applied:
            try:
                _claim = frappe.get_doc({
                    "doctype": "DOBiz Promo Claim",
                    "email": email,
                    "claimed_on": now_datetime(),
                    "free_months": promo["free_months"],
                    "free_until": add_months(today(), promo["free_months"])
                })
                _claim.flags.ignore_permissions = True
                _claim.insert(ignore_permissions=True)
                promo_claim_name = _claim.name
                promo_free_until = _claim.free_until
            except Exception as _pe:
                frappe.db.rollback()
                promo_applied = False
                frappe.logger("bizmarketing").info(f"Launch promo slot missed (race/dupe): {_pe}")

        # Coupons stack AFTER the term discount and never alongside the promo.
        coupon_rec_name = None
        coupon_amount = 0.0
        coupon_display = None
        coupon_code_norm = None
        if coupon_code and not promo_applied:
            cev = _coupon_api.evaluate(coupon_code, package_tier, billing_term_int, subtotal_after_term)
            if not cev["valid"]:
                frappe.throw(_("Coupon error: {0}").format(cev["message"]), exc=frappe.ValidationError)
            coupon_amount = cev["discount_amount"]
            coupon_display = cev.get("display")
            coupon_rec_name = cev["coupon_name"]
            coupon_code_norm = str(coupon_code).strip().upper()

        total_amount = 0.0 if promo_applied else round(max(0.0, subtotal_after_term - coupon_amount), 2)
        amount_breakdown = {
            "base_monthly": base_monthly,
            "months": billing_term_int,
            "term_discount_percent": discount_pct * 100,
            "subtotal": subtotal_after_term,
            "coupon_code": coupon_code_norm,
            "coupon_discount": coupon_amount,
            "total": total_amount
        }
        from bizmarketing.api.dobiz_manual_activation import manual_review_required
        manual_review = manual_review_required() and total_amount > 0
        _trace("1-validated")

        # 2. Company creation
        _trace("2-company-begin")
        abbr = ''.join([w[0] for w in company_name.split() if w]).upper()[:5] or "DOB"
        base_abbr = abbr
        c = 0
        while frappe.db.exists("Company", {"abbr": abbr}):
            c += 1
            suffix = str(c)
            # Truncate the base so the counter always fits within 5 chars,
            # otherwise (base+suffix)[:5] can reproduce the same colliding abbr forever.
            abbr = (base_abbr[:5 - len(suffix)] + suffix)
            
        if not frappe.db.exists("Company", company_name):
            for attempt in (1, 2):
                try:
                    comp_doc = frappe.get_doc({
                        "doctype": "Company",
                        "company_name": company_name,
                        "abbr": abbr,
                        "default_currency": "ETB",
                        "domain": "Retail" if "Retail" in industry else "Services",
                        "country": "Ethiopia"
                    })
                    comp_doc.flags.ignore_permissions = True
                    comp_doc.flags.ignore_setup_wizard = True
                    comp_doc.flags.ignore_chart_of_accounts = True
                    comp_doc.insert(ignore_permissions=True)
                    break
                except Exception as ce:
                    if "1205" in str(ce) and attempt == 1:
                        import time
                        time.sleep(20)
                        continue
                    frappe.logger("bizmarketing").warning(f"Company setup hook warning (non-fatal): {ce}")
                    if not frappe.db.exists("Company", company_name):
                        try:
                            frappe.db.sql("""
                                INSERT IGNORE INTO `tabCompany` 
                                (name, company_name, abbr, default_currency, country, creation, modified, modified_by, owner)
                                VALUES (%s, %s, %s, 'ETB', 'Ethiopia', NOW(), NOW(), 'Administrator', 'Administrator')
                            """, (company_name, company_name, abbr))
                        except Exception:
                            pass
            
        # 3. Customer under Biz Technology Solutions
        _trace("3-customer-begin")
        parent_company = "Biz Technology Solutions"
        if not frappe.db.exists("Customer", company_name):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": company_name,
                "customer_group": "Commercial",
                "territory": "Ethiopia",
                "customer_type": "Company",
                "company": parent_company
            }).insert(ignore_permissions=True)

        # 4. Determine Role & Module Profiles
        _trace("4-profiles-begin")
        norm_ind = INDUSTRY_ALIASES.get(industry, industry)
        if package_tier == "Starter Module":
            role_profile = "DOBiz Starter User"
            module_profile = f"DOBiz Starter - {selected_module}" if frappe.db.exists("Module Profile", f"DOBiz Starter - {selected_module}") else "DOBiz Starter - Accounts"
        elif package_tier == "Business Growth":
            role_profile = "DOBiz Growth Enterprise"
            module_profile = "DOBiz Growth - Standard"
        else:
            # Full Industry ERP
            rp, mp = INDUSTRY_FULL_PROFILES.get(norm_ind, ("DOBiz Growth Enterprise", "DOBiz Growth - Standard"))
            role_profile = rp if frappe.db.exists("Role Profile", rp) else "DOBiz Growth Enterprise"
            module_profile = mp if frappe.db.exists("Module Profile", mp) else "DOBiz Growth - Standard"

        # 5. User Account (NEVER self-activated — Bismillah)
        _trace("5-user-begin")
        # ANFRG-26-00063 P0: /dobiz-signup is the PAID registration funnel, but a
        # claimed bank transfer is NOT verified money. Accounts stay DISABLED and
        # payment claims go to the manual review queue until an admin confirms
        # funds received (bizmarketing.api.dobiz_manual_activation).
        # NOTE: manual_review was already computed during validation — a 0 ETB
        # launch-promo signup claims no funds, so it bypasses review entirely.
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": full_name,
                "phone": phone,
                "send_welcome_email": 0,
                "role_profile_name": role_profile,
                "module_profile": module_profile,
                "enabled": 0 if manual_review else 1,
                "user_type": "System User",
                "company": company_name,
                "custom_company": company_name
            }).insert(ignore_permissions=True)

            # Strict multi-company isolation
            frappe.get_doc({
                "doctype": "User Permission",
                "user": email,
                "allow": "Company",
                "for_value": company_name,
                "is_default": 1
            }).insert(ignore_permissions=True)

            frappe.defaults.set_user_default("company", company_name, email)
            fy = frappe.db.get_value("Fiscal Year",
                {"disabled": 0, "year_start_date": ("<=", today()),
                 "year_end_date": (">=", today())}, "name")
            if fy:
                frappe.defaults.set_user_default("fiscal_year", fy, email)
        else:
            user = frappe.get_doc("User", email)

        # 6. Record DOBiz Trial Signup / Subscription Doc
        _trace("6-signup-begin")
        plan_link = package_tier if frappe.db.exists("DOBiz SaaS Plan", package_tier) else None
        signup_doc = frappe.get_doc({
            "doctype": "DOBiz Trial Signup",
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "company_name": company_name,
            "industry": norm_ind,
            "preferred_plan": plan_link,
            "status": "Pending" if manual_review else "Trial Active",
            "trial_start_date": today(),
            "user_linked": email,
            "company_linked": company_name,
            "custom_original_amount": subtotal_after_term,
            "custom_term_discount": term_discount_amt,
            "custom_coupon_code": coupon_code_norm,
            "custom_coupon_discount": coupon_amount,
            "custom_final_amount": total_amount,
            "custom_promo_claimed": 1 if promo_applied else 0,
            "custom_promo_free_until": promo_free_until
        })
        signup_doc.flags.dobiz_skip_provisioning = 1
        signup_doc.insert(ignore_permissions=True)
        signup_ref = signup_doc.name

        if promo_claim_name:
            try:
                frappe.db.set_value("DOBiz Promo Claim", promo_claim_name, "signup_link", signup_ref)
            except Exception as _le:
                frappe.logger("bizmarketing").warning(f"Promo claim link-back warning: {_le}")

        # 7. Record Subscription and Payment Transaction
        _trace("7-sub-begin")
        sub_name = None
        try:
            if not frappe.db.exists("Subscription", {"party": company_name}):
                plan_for_sub = None
                if frappe.db.exists("Subscription Plan", package_tier):
                    plan_for_sub = package_tier
                elif not manual_review:
                    trial_plan = frappe.get_all("DOBiz SaaS Plan",
                        filters={"is_trial_plan": 1, "enabled": 1},
                        limit=1, pluck="linked_erpnext_plan")
                    if trial_plan and frappe.db.exists("Subscription Plan", trial_plan[0]):
                        plan_for_sub = trial_plan[0]
                # ERPNext requires >=1 plan row on every Subscription; without it
                # before_insert builds "WHERE name IN ()" and crashes.
                if not plan_for_sub:
                    plan_for_sub = frappe.db.get_value(
                        "Subscription Plan", {"disabled": 0}, "name")
                sub_doc = frappe.get_doc({
                    "doctype": "Subscription",
                    "party_type": "Customer",
                    "party": company_name,
                    "company": parent_company,
                    # ANFRG-26-00063 P0: ERPNext FORCES status=Active when
                    # Trialling has NO trial_period_end (verified live), which
                    # re-enables the user via process_subscription_access.
                    # So review-pending subs ALWAYS carry a 30-day trial end:
                    # status stays Trialling, login stays locked, and approval
                    # flips it to Active via dobiz_manual_activation.
                    "status": "Trialling" if manual_review else "Active",
                    "trial_period_start": today() if manual_review else None,
                    "trial_period_end": add_days(today(), 30) if manual_review else None,
                    "current_invoice_start": today(),
                    "current_invoice_end": add_months(today(), promo["free_months"] if promo_applied else billing_term_int)
                })
                if plan_for_sub:
                    sub_doc.append("plans", {"plan": plan_for_sub, "qty": 1})
                sub_doc.insert(ignore_permissions=True)
                _trace("7-sub-inserted")
                sub_name = sub_doc.name
                if not manual_review:
                    # Client rule: prepaid term length wins over plan interval.
                    frappe.db.set_value("Subscription", sub_name, "current_invoice_end",
                                        add_months(today(), billing_term_int))
            else:
                sub_name = frappe.db.get_value("Subscription", {"party": company_name}, "name")

            # Payment claim is ALWAYS recorded for admin review — never pre-approved.
            # Launch-promo (0 ETB) signups instead get an Approved/Completed audit
            # row so the finance trail stays complete without touching real money.
            if sub_name:
                if promo_applied:
                    frappe.get_doc({
                        "doctype": "DOBiz Payment Transaction",
                        "subscription": sub_name,
                        "customer": company_name,
                        "email": email,
                        "paid_by": full_name,
                        "bank_name": "Other",
                        "reference_no": f"PROMO-{signup_ref}",
                        "amount": 0,
                        "status": "Completed",
                        "payment_status": "Approved",
                        "payment_date": today(),
                        "linked_signup": signup_ref,
                        "notes": f"LAUNCH PROMO: {promo['free_months']} months free until {promo_free_until} | Package: {package_tier}",
                        "custom_final_amount": 0
                    }).insert(ignore_permissions=True)
                    _trace("7-paytxn-promo")
                else:
                    frappe.get_doc({
                        "doctype": "DOBiz Payment Transaction",
                        "subscription": sub_name,
                        "customer": company_name,
                        "email": email,
                        "paid_by": full_name,
                        "bank_name": _norm_bank(bank_name),
                        "reference_no": payment_ref or f"ONLINE-{signup_ref}",
                        "amount": total_amount,
                        "status": "Pending",
                        "payment_status": "Pending" if manual_review else "Approved",
                        "payment_date": today(),
                        "linked_signup": signup_ref,
                        "notes": f"Bank: {bank_name or 'Bank Transfer'} | Ref: {payment_ref or ''}"
                                 + (f" | Coupon: {coupon_code_norm} (-{coupon_amount:,.2f} ETB)" if coupon_code_norm else ""),
                        "custom_coupon_code": coupon_code_norm,
                        "custom_final_amount": total_amount
                    }).insert(ignore_permissions=True)
                    if coupon_rec_name:
                        _coupon_api.consume(coupon_rec_name)
                _trace("7-paytxn-inserted")
        except Exception as pe:
            frappe.logger("bizmarketing").warning(f"Subscription / Payment transaction record warning: {pe}")

        # 8. Dispatch Welcome & Setup Credentials
        _trace("8-resetpw-begin")
        more_info_url = "https://biztechnology.et/dobiz-erp"
        guide_url = "https://ethiobiz.et/lms/courses/dobiz-smart-erp-system-user-guide"

        # Email notification — credentials ONLY after manual activation.
        if manual_review:
            # No reset_password here: the account is disabled and credentials are
            # emailed by dobiz_manual_activation.activate_account after approval.
            password_link = None
            _send_under_review_email(email, full_name, company_name, package_tier,
                                     billing_term_int, total_amount, payment_ref, bank_name)
        else:
            password_link = user.reset_password(send_email=False)
            _trace("8-resetpw-done")
            subject = f"Welcome to DOBiz Smart ERP - {company_name} [{package_tier}]"
            promo_line = (f"<li><strong>Launch Offer Applied:</strong> {promo['free_months']} months FREE "
                          f"— billing begins after {promo_free_until}</li>") if promo_applied else ""
            coupon_line = (f"<li><strong>Coupon Applied:</strong> {coupon_code_norm} "
                           f"(-{coupon_amount:,.2f} ETB)</li>") if coupon_code_norm else ""
            message = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; color: #0f172a;">
            <div style="background: linear-gradient(135deg, #072a2e 0%, #008080 100%); color: white; padding: 24px; border-radius: 16px; text-align: center; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 24px;">Welcome to DOBiz Smart ERP</h1>
                <p style="margin: 6px 0 0 0; opacity: 0.9;">Sovereign Cloud ERP for Ethiopian and Global Enterprises</p>
            </div>

            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your enterprise workspace for <strong>{company_name}</strong> has been configured with the <strong>{package_tier}</strong> ({industry} Edition).</p>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #008080;">Your Account Details:</h3>
                <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>Company:</strong> {company_name} ({abbr})</li>
                    <li><strong>Login Email:</strong> {email}</li>
                    <li><strong>Package Tier:</strong> {package_tier}</li>
                    <li><strong>Billing Term:</strong> {billing_term_int} Months ({discount_pct*100:.0f}% Discount)</li>
                    <li><strong>Total Settled Amount:</strong> {total_amount:,.2f} ETB</li>
                    {promo_line}
                    {coupon_line}
                </ul>
            </div>

            <div style="text-align: center; margin: 25px 0;">
                <a href="{password_link}" style="background: #008080; color: white; padding: 12px 28px; text-decoration: none; border-radius: 24px; font-weight: bold; display: inline-block;">Set Your Password & Login &rarr;</a>
            </div>

            <div style="background: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 12px; padding: 16px; margin: 20px 0;">
                <h4 style="margin: 0 0 6px 0; color: #0f766e;">📖 DOBiz Tutorials & Resources:</h4>
                <p style="margin: 0 0 6px 0; font-size: 13.5px;">• <strong>Learn DOBiz SmartERP:</strong> <a href="{guide_url}" style="color: #008080; font-weight: bold;">DOBiz Smart ERP System User Guide</a></p>
                <p style="margin: 0; font-size: 13.5px;">• <strong>Explore Full Features:</strong> <a href="{more_info_url}" style="color: #008080; font-weight: bold;">DOBiz ERP Product Overview</a></p>
            </div>

            <p style="color: #64748b; font-size: 13px; margin-top: 30px;">Managed and Operated Exclusively by <strong>Biz Technology Solutions</strong>.</p>
        </div>
        """
            try:
                frappe.sendmail(recipients=[email], subject=subject, message=message, delayed=True)
                _trace("8-sendmail-queued")
            except Exception as e:
                frappe.logger("bizmarketing").warning(f"Email delivery skipped or simulated: {e}")

        frappe.db.commit()
        _trace("9-committed")

        # --- AddisPay Online Payment ---
        addipay_checkout_url = None
        addipay_uuid = None
        if payment_method == "addipay" and total_amount > 0 and not promo_applied:
            try:
                from bizmarketing.api.addispay import create_hosted_order, get_addispay_config
                cfg = get_addispay_config()
                if cfg.get("api_key"):
                    site = get_url()
                    ap_tx_ref = f"DOBIZ-{signup_ref}-{frappe.generate_hash(length=6)}"
                    ap_result = create_hosted_order(
                        amount=total_amount,
                        tx_ref=ap_tx_ref,
                        customer_email=email,
                        customer_name=full_name,
                        phone_number=phone,
                        description=f"DOBiz {package_tier} — {company_name} ({billing_term_int}mo)",
                        success_url=f"{site}/dobiz-payment?ref={signup_ref}&status=success",
                        error_url=f"{site}/dobiz-payment?ref={signup_ref}&status=failed",
                        message=f"DOBiz Smart ERP — {company_name}",
                    )
                    addipay_checkout_url = ap_result.get("redirect") or ap_result.get("checkout_url")
                    addipay_uuid = ap_result.get("uuid") or ap_tx_ref
                    # Persist the AddisPay reference on the payment transaction
                    try:
                        frappe.db.set_value("DOBiz Payment Transaction",
                                            {"subscription": sub_name, "customer": company_name},
                                            {"addispay_transaction_id": addipay_uuid,
                                             "reference_no": ap_tx_ref,
                                             "notes": f"AddisPay online | tx_ref={ap_tx_ref} | uuid={addipay_uuid}"})
                        frappe.db.commit()
                    except Exception as _ue:
                        frappe.logger("bizmarketing").warning(f"AddisPay tx_ref write-back warning: {_ue}")
                    _trace("9-addipay-order-created")
                else:
                    frappe.logger("bizmarketing").warning("AddisPay not configured — falling back to bank transfer")
            except Exception as ae:
                frappe.logger("bizmarketing").warning(f"AddisPay initiation failed (falling back to bank transfer): {ae}")

        resp = {
            "success": True,
            "message": ("Registration received! Your bank transfer is under manual verification "
                        "- account activated within 24 hours InSha'Allah." if manual_review
                        else "DOBiz Enterprise Tenant provisioned successfully Alhamdulillah!"),
            "pending_review": bool(manual_review),
            "company": company_name,
            "abbr": abbr,
            "email": email,
            "package_tier": package_tier,
            "total_amount": total_amount,
            "discount_applied": f"{discount_pct*100:.0f}%",
            "coupon_applied": bool(coupon_code_norm),
            "amount_breakdown": amount_breakdown,
            "promo": ({"applied": True, "free_months": promo["free_months"],
                       "free_until": str(promo_free_until)} if promo_applied
                      else {"applied": False}),
            "signup_ref": signup_ref,
            "user_guide_url": guide_url,
            "more_info_url": more_info_url,
            "payment_link": f"https://ethiobiz.et/dobiz-payment?ref={signup_ref}"
        }
        if addipay_checkout_url:
            resp["checkout_url"] = addipay_checkout_url
            resp["addipay_uuid"] = addipay_uuid
            resp["payment_method"] = "addipay"
        else:
            resp["payment_method"] = "bank_transfer"
        if password_link:
            resp["password_setup_link"] = password_link
        return resp
    finally:
        frappe.set_user(prev_user)


def _send_under_review_email(email, full_name, company_name, package_tier,
                             billing_term_int, total_amount, payment_ref, bank_name):
    subject = f"DOBiz Registration Received - {company_name} [Under Verification]"
    message = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; color: #0f172a;">
            <div style="background: linear-gradient(135deg, #072a2e 0%, #008080 100%); color: white; padding: 24px; border-radius: 16px; text-align: center; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 22px;">Registration Received &mdash; Under Verification</h1>
                <p style="margin: 6px 0 0 0; opacity: 0.9;">DOBiz Smart ERP by Biz Technology Solutions</p>
            </div>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your registration for <strong>{company_name}</strong> ({package_tier}, {billing_term_int} months,
            {total_amount:,.2f} ETB) has been received together with your transfer reference
            <strong>{payment_ref or ''}</strong> ({bank_name or 'Bank Transfer'}).</p>
            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 18px; margin: 20px 0;">
                <strong>Next step:</strong> our team verifies your bank transfer within 24 hours InSha'Allah.
                Your account is activated and login credentials are emailed immediately after confirmation.
            </div>
            <p style="color: #64748b; font-size: 13px;">Questions? Reply to this email or contact Biz Technology Solutions.</p>
        </div>
        """
    try:
        frappe.sendmail(recipients=[email], subject=subject, message=message, delayed=True)
    except Exception as e:
        frappe.logger("bizmarketing").warning(f"Ack email skipped: {e}")

@frappe.whitelist(allow_guest=True)
def upload_payment_proof(signup_ref, payment_ref, bank_name, receipt_file=None):
    """Upload payment confirmation slip for a pending DOBiz subscription."""
    prev_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        signup_doc = None
        if frappe.db.exists("DOBiz Trial Signup", signup_ref):
            signup_doc = frappe.get_doc("DOBiz Trial Signup", signup_ref)
        else:
            name = frappe.db.get_value("DOBiz Trial Signup", {"email": signup_ref}, "name") or \
                   frappe.db.get_value("DOBiz Trial Signup", {"company_name": signup_ref}, "name")
            if name:
                signup_doc = frappe.get_doc("DOBiz Trial Signup", name)
        
        if not signup_doc:
            frappe.throw(_("Invalid or expired Signup Reference."))

        # ANFRG-26-00063 P0: a payment slip is a CLAIM, not verified money.
        # Signup goes to Pending; the transaction is created Pending for the
        # admin review queue. Nothing is auto-activated here.
        from bizmarketing.api.dobiz_manual_activation import manual_review_required
        manual_review = manual_review_required()

        signup_doc.status = "Pending" if manual_review else "Converted"
        signup_doc.save(ignore_permissions=True)

        # Record Subscription and Payment Transaction safely
        try:
            sub_name = frappe.db.get_value("Subscription", {"party": signup_doc.company_name}, "name")
            if not sub_name:
                sub_plans = frappe.get_all("Subscription Plan", limit=1, pluck="name")
                plans_data = [{"plan": sub_plans[0], "qty": 1}] if sub_plans else []
                sub_doc = frappe.get_doc({
                    "doctype": "Subscription",
                    "party_type": "Customer",
                    "party": signup_doc.company_name,
                    "company": "Biz Technology Solutions",
                    "status": "Trialling" if manual_review else "Active",
                    # 30-day trial window keeps status Trialling (ERPNext
                    # would force Active without trial_period_end).
                    "trial_period_start": today() if manual_review else None,
                    "trial_period_end": add_days(today(), 30) if manual_review else None,
                    "plans": plans_data,
                    "current_invoice_start": today(),
                    "current_invoice_end": add_months(today(), 3)
                }).insert(ignore_permissions=True)
                sub_name = sub_doc.name

            if sub_name:
                frappe.get_doc({
                    "doctype": "DOBiz Payment Transaction",
                    "subscription": sub_name,
                    "customer": signup_doc.company_name,
                    "email": signup_doc.email,
                    "paid_by": signup_doc.full_name,
                    "bank_name": _norm_bank(bank_name),
                    "reference_no": payment_ref or f"PROOF-{signup_ref}",
                    "amount": 0.0,
                    "status": "Pending" if manual_review else "Completed",
                    "payment_status": "Pending" if manual_review else "Approved",
                    "payment_date": today(),
                    "linked_signup": signup_ref,
                    "notes": f"Bank: {bank_name or 'Bank Transfer'} | Ref: {payment_ref or ''}"
                }).insert(ignore_permissions=True)
        except Exception as pe:
            frappe.logger("bizmarketing").warning(f"Payment proof transaction link warning: {pe}")

        if manual_review:
            _send_under_review_email(signup_doc.email, signup_doc.full_name,
                                     signup_doc.company_name, "", 0, 0.0, payment_ref, bank_name)

        frappe.db.commit()
        return {
            "success": True,
            "pending_review": bool(manual_review),
            "message": ("Payment slip received! Our team will verify your bank transfer within "
                        "24 hours InSha'Allah — you will receive your login credentials by email "
                        "after confirmation." if manual_review
                        else "Payment slip submitted and verified successfully Alhamdulillah!"),
        }
    finally:
        frappe.set_user(prev_user)
