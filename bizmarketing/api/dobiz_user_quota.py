# Bismillah - DOBiz subscription-based USER QUOTA enforcement.
# A company's user count is defined by its subscription package (max_users).
# These hooks run on User.validate and User Permission.validate and block
# adding any user to a DOBiz tenant company that is already at its cap.
#
# Design contract (see PRD 2026-09-11, section 4.4 / FR-7):
#   1. User.company / User.custom_company = the user's DEFAULT company.
#   2. A user may hold MULTIPLE companies via User Permission rows
#      (allow="Company"); each company is gated by ITS OWN subscription cap.
#   3. Cap is resolved dynamically from the company's subscription package.
#   4. Owner (signing email), System Managers/Administrators and non-DOBiz
#      companies are never blocked. max_users == 0 means unlimited.
#   5. Downgrades never lock out existing staff; only NEW adds are gated.
import frappe

# Documented fallbacks (kept in sync with dobiz_signup_api.PACKAGE_CONFIG and
# the DOBiz SaaS Plan seeds). 0 = unlimited.
TIER_DEFAULT_MAX_USERS = {
    "Starter Module": 3,
    "Business Growth": 10,
    "Full Industry ERP Package": 0,  # Unlimited
}

PLAN_FALLBACK_MAX_USERS = {
    "DOBiz Trial Plan": 1,
    "DOBiz Standard Plan": 5,
    "DOBiz Premium Plan": 0,  # Unlimited
}


def _log(msg):
    frappe.logger("bizmarketing").info(f"[dobiz_user_quota] {msg}")


def is_admin_user(email=None):
    email = email or frappe.session.user
    if not email:
        return False
    if email == "Administrator":
        return True
    try:
        roles = set(frappe.get_roles(email))
    except Exception:
        return False
    return bool(roles & {"System Manager", "Administrator"})


def is_dobiz_tenant(company):
    if not company or not str(company).strip():
        return False
    return bool(frappe.db.get_value(
        "DOBiz Trial Signup", {"company_name": company}, "name"))


def get_company_signup(company):
    return frappe.db.get_value(
        "DOBiz Trial Signup", {"company_name": company},
        ["name", "email", "industry", "custom_package_tier"],
        as_dict=True)


def _first_value(settings_rows, package_tier, industry, field):
    """Find package row for tier+industry (exact industry match wins,
    then global blank-industry default row)."""
    ind = (industry or "").strip()
    for r in settings_rows or []:
        if r.get("package_tier") != package_tier:
            continue
        if r.get("enabled") is False or r.get("enabled") == 0:
            continue
        if (r.get("industry") or "").strip() == ind and r.get(field) is not None:
            return r.get(field)
    for r in settings_rows or []:
        if r.get("package_tier") != package_tier:
            continue
        if r.get("enabled") is False or r.get("enabled") == 0:
            continue
        if not (r.get("industry") or "").strip() and r.get(field) is not None:
            return r.get(field)
    return None


def get_company_user_limit(company):
    """Dynamic user cap for a DOBiz tenant company. None = not a tenant;
    0 = unlimited. Resolution order: linked DOBiz SaaS Plan -> plan by tier
    name -> table package row -> documented fallback."""
    if not is_dobiz_tenant(company):
        return None
    signup = get_company_signup(company)
    industry = (signup.get("industry") if signup else "") or ""
    tier = (signup.get("custom_package_tier") if signup else "") or ""

    plan_name = None
    sub = frappe.db.get_value(
        "Subscription", {"party": company}, "name")
    if sub:
        plan_name = frappe.db.get_value(
            "Subscription Plan Detail",
            {"parenttype": "Subscription", "parent": sub}, "plan")

    if plan_name:
        dobiz_max = frappe.db.get_value(
            "DOBiz SaaS Plan", {"linked_erpnext_plan": plan_name}, "max_users")
        if dobiz_max is not None:
            return int(dobiz_max or 0)
    if tier:
        dobiz_max = frappe.db.get_value(
            "DOBiz SaaS Plan", {"plan_name": tier}, "max_users")
        if dobiz_max is not None:
            return int(dobiz_max or 0)
        try:
            from bizmarketing.api import dobiz_signup_config as _cfg
            st = _cfg.get_signup_settings()
        except Exception as e:
            _log(f"config load warning: {e}")
            st = None
        if st:
            v = _first_value(st.get("package_items"), tier, industry,
                             "max_users")
            if v is not None:
                return int(v or 0)
    if plan_name and plan_name in PLAN_FALLBACK_MAX_USERS:
        return PLAN_FALLBACK_MAX_USERS[plan_name]
    if tier and tier in TIER_DEFAULT_MAX_USERS:
        return TIER_DEFAULT_MAX_USERS[tier]
    return 0  # Unknown config -> open (never over-block)


def user_has_company(email, company):
    """True when the user already has access to the company (via a permission
    row, their own company/custom_company field, or user defaults)."""
    if not email or not company:
        return False
    if frappe.db.exists("User Permission",
                        {"user": email, "allow": "Company",
                         "for_value": company}):
        return True
    if frappe.db.exists("User", email):
        uco = frappe.db.get_value(
            "User", email, ["company", "custom_company"], as_dict=True)
        if uco and (uco.get("company") == company or
                    uco.get("custom_company") == company):
            return True
    dv = frappe.db.get_value("DefaultValue",
                             {"parent": email, "defkey": "company"},
                             "defvalue")
    return dv == company


def count_company_users(company):
    """Distinct users that can access the company = seats used.
    Counted via User Permission (allow=Company) union users whose
    company/custom_company equals the company. Includes disabled seats."""
    perms = frappe.db.sql("""
        SELECT COUNT(DISTINCT user) FROM `tabUser Permission`
        WHERE `allow` = 'Company' AND for_value = %s
    """, (company,))[0][0]
    fields = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabUser`
        WHERE `company` = %s OR `custom_company` = %s
    """, (company, company))[0][0]
    return int(max(perms, fields))


def is_tenant_owner(email, company):
    signup = get_company_signup(company)
    return bool(signup and signup.get("email") and
                email and signup["email"].strip().lower() == email.strip().lower())


def assert_user_append_within_cap(company, add_email, is_new_user=False,
                                  role_profile_hint=None):
    """Raise if adding `add_email` to a DOBiz tenant company would exceed the
    package user cap. No-op for non-tenants, admins, owners and re-adds."""
    if not company or not add_email:
        return
    limit = get_company_user_limit(company)
    if limit is None:
        return
    if is_admin_user(add_email):
        return
    # A NEW user's roles are not resolvable yet at validate time; use the
    # requested role profile as the admin probe (System-Manager provisioning).
    if role_profile_hint and ("System Manager" in role_profile_hint or
                              "Administrator" in role_profile_hint):
        return
    if is_tenant_owner(add_email, company):
        return
    if user_has_company(add_email, company):
        return
    used = count_company_users(company)
    if used + 1 > limit:
        disp = "unlimited" if limit == 0 else str(limit)
        frappe.throw(
            f"DOBiz subscription limit reached for {company}: "
            f"this package permits {disp} user(s), and {used} are already "
            f"assigned. Upgrade the subscription package to add more users, "
            f"or raise Max Users on the package in DOBiz SaaS Settings.",
            frappe.ValidationError)


def validate_user_cap(doc, method=None):
    """User.validate hook - checks the user's own + granted tenant companies."""
    try:
        if not getattr(doc, "email", None) or not doc.is_new():
            return
        if is_admin_user(doc.email):
            return
        companies = set()
        for f in ("company", "custom_company"):
            v = doc.get(f)
            if v:
                companies.add(v)
        for row in (doc.get("user_permissions") or []):
            if (row.get("allow") == "Company" and row.get("for_value")):
                companies.add(row.get("for_value"))
        for co in companies:
            assert_user_append_within_cap(co, doc.email, is_new_user=True,
                                          role_profile_hint=doc.get("role_profile_name"))
    except frappe.ValidationError:
        raise
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_user_quota] User validate guard skipped: {e}")


def validate_user_permission_cap(doc, method=None):
    """User Permission.validate hook - gates each new Company access grant."""
    try:
        if doc.get("allow") != "Company" or not doc.get("for_value"):
            return
        assert_user_append_within_cap(doc.get("for_value"), doc.get("user"))
    except frappe.ValidationError:
        raise
    except Exception as e:
        frappe.logger("bizmarketing").warning(
            f"[dobiz_user_quota] User Permission guard skipped: {e}")


# Convenience for tooling / tests
@frappe.whitelist()
def company_user_quota_dashboard(company=None):
    if company:
        companies = [company]
    else:
        companies = frappe.get_all(
            "DOBiz Trial Signup", pluck="company_name")
    out = []
    for co in companies:
        limit = get_company_user_limit(co)
        if limit is None:
            continue
        out.append({
            "company": co,
            "max_users": limit,
            "users_used": count_company_users(co),
            "remaining": None if limit == 0 else max(0, limit - count_company_users(co)),
        })
    return {"companies": out}