import frappe
from frappe.utils import today, add_days, getdate

def _get_fiscal_year():
    fy = frappe.db.get_value("Fiscal Year",
        {"disabled": 0, "year_start_date": ("<=", getdate()), "year_end_date": (">=", getdate())},
        "name")
    return fy or str(getdate().year)

CHILD_TABLES_WITH_COMPANY = [
    "tabAccounting Dimension Detail", "tabAllowed To Transact With",
    "tabAsset Movement Item", "tabCustomer Credit Limit",
    "tabExpense Claim Account", "tabFee Category Default",
    "tabFiscal Year Company", "tabItem Default",
    "tabLedger Health Monitor Company", "tabMode of Payment Account",
    "tabParty Account", "tabSalary Component Account",
    "tabTax Withholding Account", "tabWork Experience",
]

def _clean_orphaned_company_data():
    for t in CHILD_TABLES_WITH_COMPANY:
        frappe.db.sql(f"""DELETE FROM `{t}` WHERE company IS NOT NULL
            AND company != '' AND company NOT IN (SELECT name FROM `tabCompany`)""")
    for t in ["tabAccount", "tabCost Center", "tabWarehouse"]:
        frappe.db.sql(f"""DELETE FROM `{t}` WHERE company IS NOT NULL
            AND company != '' AND company NOT IN (SELECT name FROM `tabCompany`)""")

def _create_company_fast(company_name, abbr, industry=None):
    """Create a tenant Company WITHOUT chart-of-accounts side effects.

    on_update() checks the GLOBAL frappe.local.flags.ignore_chart_of_accounts
    (a doc-level flag is ignored there), so ERPNext runs
    create_default_tax_template() against a bank-less chart and raises
    `IndexError: list index out of range`. Set the global flag for the insert,
    and fall back to a bare row if any hook still complains (mirrors the
    proven paid-signup path). Returns True when the Company exists.
    """
    if frappe.db.exists("Company", company_name):
        return True
    had_flag = getattr(frappe.local.flags, "ignore_chart_of_accounts", None)
    frappe.local.flags.ignore_chart_of_accounts = True
    try:
        domain = "Retail" if "Retail" in (industry or "") else "Services"
        company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": abbr,
            "default_currency": "ETB",
            "domain": domain,
            "country": "Ethiopia"
        })
        company_doc.flags.ignore_permissions = True
        company_doc.flags.ignore_setup_wizard = True
        company_doc.flags.ignore_chart_of_accounts = True
        company_doc.flags.ignore_validate = True
        company_doc.insert(ignore_permissions=True)
    except Exception as ce:
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
    finally:
        if had_flag is not None:
            frappe.local.flags.ignore_chart_of_accounts = had_flag
        elif hasattr(frappe.local.flags, "ignore_chart_of_accounts"):
            del frappe.local.flags.ignore_chart_of_accounts
    return frappe.db.exists("Company", company_name) is not None


def validate_trial_signup(doc, method=None):
    mandatory_fields = {"full_name": "Full Name", "email": "Email", "phone": "Phone", "company_name": "Company Name"}
    missing = []
    for field, label in mandatory_fields.items():
        if not doc.get(field):
            missing.append(label)
    if missing:
        frappe.throw(f"Missing mandatory fields: {', '.join(missing)}")
    if doc.email and doc.is_new():
        existing = frappe.db.get_value("DOBiz Trial Signup",
            {"email": doc.email, "name": ("!=", doc.name if doc.name else "")})
        if existing:
            frappe.throw(f"A signup with email {doc.email} already exists.")

def _trace(tag):
    import time as _t
    print(f"[DOBIZ-TRIAL-TRACE] {tag} t={round(_t.time())}", flush=True)

def setup_trial_tenant(doc, method=None):
    if doc.flags.get("dobiz_skip_provisioning"):
        frappe.logger("bizmarketing").info(
            f"Skipping hook provisioning for {doc.email} (API path handles it)")
        return
    frappe.logger("bizmarketing").info(f"Bismillah. Starting Trial Onboarding for: {doc.email}")
    try:
        _clean_orphaned_company_data()
        frappe.logger("bizmarketing").info("Cleaned orphaned company references before provisioning")
    except Exception:
        frappe.logger("bizmarketing").warning("Orphaned data cleanup failed (non-fatal, continuing)")
    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    doc.db_set("trial_start_date", today())
    doc.db_set("status", "Trial Active")
    company_name = doc.company_name
    abbr = ''.join([w[0] for w in company_name.split() if w]).upper()[:5]
    if not abbr:
        abbr = "TRL"
    base_abbr = abbr
    counter = 0
    while frappe.db.exists("Company", {"abbr": abbr}):
        counter += 1
        suffix = str(counter)
        # Truncate base so the counter always fits within 5 chars,
        # otherwise (base+suffix)[:5] can reproduce the same colliding abbr forever.
        abbr = (base_abbr[:5 - len(suffix)] + suffix)
    prev_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        _create_company_fast(company_name, abbr, doc.get("industry"))
        if not frappe.db.exists("Company", company_name):
            frappe.logger("bizmarketing").error(
                f"Trial provisioning FAILED for {doc.email}: Company creation error"); _trace("ERR-COMPANY create failed")
            doc.db_set("status", "Failed")
            return
        frappe.logger("bizmarketing").info(f"Created Tenant Company: {company_name} ({abbr})")
        try:
            from bizmarketing.api.dobiz_fiscal_year import ensure_company_fiscal_year
            fy_name = ensure_company_fiscal_year(company_name)
            frappe.logger("bizmarketing").info(f"Company {company_name} wired to Fiscal Year {fy_name}")
        except Exception as e:
            frappe.logger("bizmarketing").warning(f"Fiscal Year link warning (non-fatal): {e}")
        customer_name = company_name
        if not frappe.db.exists("Customer", customer_name):
            try:
                frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": "Commercial",
                    "territory": "Ethiopia",
                    "customer_type": "Company",
                    "company": parent_company
                }).insert(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Created Customer: {customer_name}")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to create Customer: {e}"); _trace(f"ERR-CUSTOMER {e}")
        role_profile, module_profile = _get_industry_profiles(doc.industry, settings)
        # ANFRG-26-00063 P0: trial accounts are also provisioned DISABLED when
        # manual review is enforced. Admin activates via
        # bizmarketing.api.dobiz_manual_activation.activate_account (or by
        # approving a payment) — credentials are emailed only at that point.
        from bizmarketing.api.dobiz_manual_activation import manual_review_required
        manual_review = manual_review_required()
        # Self-serve trial (ethiobiz.et/trial): when allow_self_serve_trial is
        # enabled the trial is usable immediately — no human review gate, even
        # if bank-payment manual review is enforced for paid signups.
        self_serve = bool(getattr(settings, "allow_self_serve_trial", False))
        review_to_apply = manual_review and not self_serve
        if not frappe.db.exists("User", doc.email):
            try:
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": doc.email,
                    "first_name": doc.full_name,
                    "last_name": doc.get("last_name") or "",
                    "phone": doc.phone,
                    "send_welcome_email": 0,
                    "role_profile_name": role_profile,
                    "module_profile": module_profile,
                    "enabled": 0 if review_to_apply else 1,
                    "company": company_name,
                    "custom_company": company_name
                })
                user.insert(ignore_permissions=True)
                frappe.get_doc({
                    "doctype": "User Permission",
                    "user": user.name,
                    "allow": "Company",
                    "for_value": company_name,
                }).insert(ignore_permissions=True)
                doc.db_set("user_linked", user.name)
                doc.db_set("company_linked", company_name)
                fy = _get_fiscal_year()
                frappe.defaults.set_user_default("fiscal_year", fy, user.name)
                frappe.defaults.set_user_default("company", company_name, user.name)
                try:
                    from bizmarketing.api.dobiz_fiscal_year import ensure_company_fiscal_year
                    ensure_company_fiscal_year(company_name, email=user.name)
                except Exception as e:
                    frappe.logger("bizmarketing").warning(f"Fiscal Year default warning (non-fatal): {e}")
                frappe.logger("bizmarketing").info(f"User {doc.email} provisioned with {role_profile}/{module_profile}, FY={fy}")
            except Exception as e:
                frappe.logger("bizmarketing").error(f"Failed to create User: {e}"); _trace(f"ERR-USER {e}")
                doc.db_set("status", "Failed")
                return
        trial_plan = frappe.get_all("DOBiz SaaS Plan", filters={"is_trial_plan": 1, "enabled": 1}, limit=1)
        trial_duration = settings.default_trial_duration_days or 7
        plan_name = None
        if trial_plan:
            plan_doc = frappe.get_doc("DOBiz SaaS Plan", trial_plan[0].name)
            plan_name = plan_doc.linked_erpnext_plan or f"DOBiz {plan_doc.plan_name}"
            trial_duration = plan_doc.trial_duration_days or trial_duration
        try:
            if not plan_name or not frappe.db.exists("Subscription Plan", plan_name):
                plan_name = frappe.db.get_value("Subscription Plan", {"disabled": 0}, "name")
            subs = frappe.new_doc("Subscription")
            subs.party_type = "Customer"
            subs.party = customer_name
            subs.company = parent_company
            subs.trial_period_start = today()
            subs.trial_period_end = add_days(today(), trial_duration)
            if plan_name:
                subs.append("plans", {"plan": plan_name, "qty": 1})
            subs.insert(ignore_permissions=True)
            doc.db_set("subscription_link", subs.name)
            frappe.logger("bizmarketing").info(f"Trial Subscription {subs.name} for {customer_name} ({trial_duration} days)")
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to generate Subscription: {e}")
        try:
            if review_to_apply:
                # Acknowledgment only — credentials emailed after manual activation.
                from bizmarketing.api.dobiz_signup_api import _send_under_review_email
                _send_under_review_email(doc.email, doc.full_name, company_name,
                                         "Trial", 0, 0.0, None, None)
            else:
                from bizmarketing.api.subscription_notifications import send_welcome_email
                password_link = user.reset_password(send_email=False)
                send_welcome_email(doc.email, doc.full_name, company_name, password_setup_link=password_link)
        except Exception as e:
            frappe.logger("bizmarketing").error(f"Failed to send welcome email: {e}")
        try:
            # Stamp the trial package for the quota/cap engine.
            doc.db_set("custom_package_tier", "DOBiz Trial Plan")
            doc.db_set("custom_max_users", 1)
        except Exception as _se:
            frappe.logger("bizmarketing").warning(f"Trial package stamp warning: {_se}")
    finally:
        frappe.set_user(prev_user)
    frappe.db.commit()
    frappe.logger("bizmarketing").info(f"Alhamdulillah. Trial onboarding complete for {doc.email}")

def process_subscription_access(doc, method=None):
    from bizmarketing.api.dobiz_manual_activation import manual_review_required

    settings = frappe.get_single("DOBiz SaaS Settings")
    parent_company = settings.parent_company or "Biz Technology Solutions"
    if doc.company != parent_company:
        return
    frappe.logger("bizmarketing").info(f"Processing Access for Subscription: {doc.name} (Status: {doc.status})")
    trial_docs = frappe.get_all("DOBiz Trial Signup", filters={"company_name": doc.party}, fields=["email"])
    if not trial_docs:
        return
    target_email = trial_docs[0].email
    if not frappe.db.exists("User", target_email):
        return
    try:
        user = frappe.get_doc("User", target_email)
        if doc.status == "Active":
            # ANFRG-26-00063 P0 (defense-in-depth): when manual review is
            # enforced, ONLY dobiz_manual_activation may enable an account.
            # Any signup state other than Converted (Pending, Failed, Trial
            # Active, ...) means the bank claim was never vetted — this hook
            # must not enable anyone, regardless of how the status got there
            # (including ERPNext forcing Trialling subs to Active).
            if manual_review_required():
                signup_status = frappe.db.get_value("DOBiz Trial Signup",
                    {"company_name": doc.party}, "status")
                if signup_status != "Converted":
                    frappe.logger("bizmarketing").warning(
                        f"Blocked auto-enable for {target_email}: "
                        f"signup status '{signup_status}' is not vetted")
                    return
            if user.enabled == 0:
                user.enabled = 1
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Re-activated access for {target_email}")
        elif doc.status in ["Unpaid", "Cancelled", "Past Due Date", "Expired"]:
            if user.enabled == 1:
                user.enabled = 0
                user.save(ignore_permissions=True)
                frappe.logger("bizmarketing").info(f"Deactivated access for {target_email}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Error toggling access for {target_email}: {e}")

def _get_industry_profiles(industry, settings=None):
    ind = (industry or "").strip()
    if not settings:
        settings = frappe.get_single("DOBiz SaaS Settings")
    tbl = getattr(settings, "trial_industry_profiles", None)
    if tbl:
        for mapping in tbl:
            enabled = getattr(mapping, "enabled", 1)
            if not enabled:
                continue
            if (getattr(mapping, "industry", "") or "").strip() != ind:
                continue
            rp = getattr(mapping, "role_profile", None)
            mp = getattr(mapping, "module_profile", None)
            if rp and frappe.db.exists("Role Profile", rp):
                if mp and not frappe.db.exists("Module Profile", mp):
                    mp = None
                return rp, mp
    try:
        from bizmarketing.api.dobiz_signup_config import get_industry_role_profiles
        rp, mp = get_industry_role_profiles(industry, "Full Industry ERP Package", settings)
        if rp and frappe.db.exists("Role Profile", rp):
            if mp and frappe.db.exists("Module Profile", mp):
                return rp, mp
            return rp, "DOBiz Growth - Standard"
    except Exception as e:
        frappe.logger("bizmarketing").warning(f"Trial profile resolution warning: {e}")
    if settings and settings.industry_role_mappings:
        for mapping in settings.industry_role_mappings:
            if mapping.industry == industry:
                return mapping.role_profile, mapping.module_profile
    return settings.default_role_profile_fallback or "Kistet DGM", settings.default_module_profile_fallback or "Biz Service"

