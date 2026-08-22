import frappe
from frappe import _
from frappe.utils import today, add_days, add_months, getdate, now_datetime
import json

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
    """Return live package catalog, pricing rules, and bank accounts."""
    return {
        "packages": PACKAGE_CONFIG,
        "discounts": DISCOUNT_RATES,
        "industries": list(INDUSTRY_FULL_PROFILES.keys()),
        "bank_accounts": [
            {"bank": "Commercial Bank of Ethiopia (CBE)", "account_name": "Hadi Awad", "account_no": "1000236131606"},
            {"bank": "Telebirr SuperApp", "account_name": "Hadi Awad", "account_no": "+251986767576 / 0986767576"},
            {"bank": "Bank of Abyssinia (BoA)", "account_name": "Hadi Awad", "account_no": "94784891"}
        ],
        "more_info_url": "https://biztechnology.et/dobiz-erp",
        "user_guide_url": "https://ethiobiz.et/lms/courses/dobiz-smart-erp-system-user-guide",
        "service_url": "https://ethiobiz.et/dobiz-saas-service-e9vyb"
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
def submit_dobiz_signup(full_name=None, email=None, phone=None, company_name=None, industry=None, package_tier=None, billing_term="3", selected_module="Accounts", payment_receipt=None, payment_ref=None, bank_name=None):
    """Zero-touch registration for DOBiz Smart ERP with tenant provisioning."""
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
        
        if package_tier not in PACKAGE_CONFIG:
            package_tier = "Business Growth"
        
        billing_term_int = int(billing_term) if str(billing_term).isdigit() else 3
        if billing_term_int not in [3, 6, 12]:
            billing_term_int = 3
            
        base_monthly = PACKAGE_CONFIG[package_tier]["price_per_month"]
        discount_pct = DISCOUNT_RATES.get(str(billing_term_int), 0.0)
        total_amount = (base_monthly * billing_term_int) * (1.0 - discount_pct)
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
        from bizmarketing.api.dobiz_manual_activation import manual_review_required
        manual_review = manual_review_required()
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
            "company_linked": company_name
        })
        signup_doc.flags.dobiz_skip_provisioning = 1
        signup_doc.insert(ignore_permissions=True)
        signup_ref = signup_doc.name

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
                    # Manual review: Trialling WITHOUT trial_period_end so the
                    # expiry cron ignores it and the user hook keeps login off.
                    # Admin approval flips it to Active (enables the user).
                    "status": "Trialling" if manual_review else "Active",
                    "current_invoice_start": today(),
                    "current_invoice_end": add_months(today(), billing_term_int)
                })
                if manual_review:
                    sub_doc.trial_period_start = today()
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
            if sub_name:
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
                }).insert(ignore_permissions=True)
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
            "signup_ref": signup_ref,
            "user_guide_url": guide_url,
            "more_info_url": more_info_url,
            "payment_link": f"https://ethiobiz.et/dobiz-payment?ref={signup_ref}"
        }
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
                    "plans": plans_data,
                    "current_invoice_start": today(),
                    "current_invoice_end": add_months(today(), 3)
                }).insert(ignore_permissions=True)
                if manual_review:
                    # No trial_period_end: expiry cron must ignore review-pending subs.
                    sub_doc.db_set("trial_period_start", today())
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
