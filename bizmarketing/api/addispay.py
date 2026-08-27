# BISMALLAH — Official AddisPay Hosted Checkout client (UAT + Production)
# Docs: https://devportal.addispay.et/docs/hosted-checkout
import json
import frappe
import requests
from frappe.utils import now_datetime, get_url, cint, cstr

UAT_BASE = "https://uat.api.addispay.et"
PROD_BASE = "https://api.addispay.et"
CREATE_ORDER_PATH = "/checkout-api/v1/create-order"


def _settings():
    return frappe.get_single("DOBiz SaaS Settings")


def _magala_settings():
    try:
        if frappe.db.exists("DocType", "Magala Checkout Settings"):
            return frappe.get_single("Magala Checkout Settings")
    except Exception:
        return None
    return None


def _password(doc, field):
    if not doc or not getattr(doc, field, None):
        return None
    try:
        return doc.get_password(field)
    except Exception:
        return None


def get_addispay_config():
    """Merge Magala Checkout Settings (user-customizable) with DOBiz SaaS Settings."""
    magala = _magala_settings()
    dobiz = _settings()
    use_dobiz = True if not magala else bool(cint(getattr(magala, "use_dobiz_addispay_credentials", 1)))

    api_key = None
    secret = None
    if not use_dobiz and magala:
        api_key = _password(magala, "addispay_api_key")
        secret = _password(magala, "addispay_webhook_secret")
    if not api_key:
        api_key = _password(dobiz, "addispay_api_key")
    if not secret:
        secret = _password(dobiz, "addispay_webhook_secret")

    sandbox = True
    if magala and getattr(magala, "addispay_sandbox_mode", None) is not None:
        sandbox = bool(cint(magala.addispay_sandbox_mode))
    else:
        try:
            sandbox = bool(cint(dobiz.addispay_sandbox_mode))
        except Exception:
            sandbox = True

    uat = (getattr(magala, "addispay_uat_base_url", None) if magala else None) or UAT_BASE
    prod = (getattr(magala, "addispay_prod_base_url", None) if magala else None) or PROD_BASE
    path = (getattr(magala, "addispay_create_order_path", None) if magala else None) or CREATE_ORDER_PATH
    if path and not path.startswith("/"):
        path = "/" + path

    def _url_tpl(field, fallback):
        raw = (getattr(magala, field, None) if magala else None) or ""
        return raw.strip() or fallback

    site = get_url()
    return {
        "api_key": api_key,
        "sandbox": sandbox,
        "base_url": (uat if sandbox else prod).rstrip("/"),
        "create_order_path": path,
        "webhook_secret": secret,
        "currency": (getattr(magala, "currency", None) if magala else None) or "ETB",
        "session_expired": (getattr(magala, "addispay_session_expired", None) if magala else None) or "5000",
        "checkout_message": (getattr(magala, "addispay_checkout_message", None) if magala else None) or "Magala marketplace payment",
        "default_phone": (getattr(magala, "addispay_default_phone", None) if magala else None) or "251911000000",
        "success_url_tpl": _url_tpl("success_url", f"{site}/magala-payment-success?tx_ref={{tx_ref}}"),
        "error_url_tpl": _url_tpl("error_url", f"{site}/magala-payment-failed?tx_ref={{tx_ref}}"),
        "cancel_url_tpl": _url_tpl("cancel_url", ""),
        "redirect_url_tpl": _url_tpl("redirect_url", ""),
        "enable_addispay": True if not magala else bool(cint(magala.enable_addispay)),
    }


def _require_api_key():
    cfg = get_addispay_config()
    if not cfg["api_key"]:
        frappe.throw("AddisPay API key not configured in DOBiz SaaS Settings")
    return cfg


def _split_name(full_name):
    name = (full_name or "Magala Customer").strip() or "Magala Customer"
    parts = name.split(None, 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else "Buyer"
    return first[:80], last[:80]


def create_hosted_order(
    amount,
    tx_ref,
    customer_email,
    customer_name,
    phone_number=None,
    description=None,
    success_url=None,
    error_url=None,
    cancel_url=None,
    redirect_url=None,
    message="EthioBiz Magala checkout",
):
    """POST /checkout-api/v1/create-order. Returns dict with checkout_url, uuid, redirect."""
    cfg = _require_api_key()
    amount_val = float(amount or 0)
    if amount_val <= 0:
        frappe.throw("Payment amount must be greater than zero")

    def _fill(tpl, fallback):
        raw = (tpl or "").replace("{tx_ref}", tx_ref)
        return raw or fallback

    site = get_url()
    success_url = success_url or _fill(cfg.get("success_url_tpl"), f"{site}/magala-payment-success?tx_ref={tx_ref}")
    error_url = error_url or _fill(cfg.get("error_url_tpl"), f"{site}/magala-payment-failed?tx_ref={tx_ref}")
    cancel_url = cancel_url or _fill(cfg.get("cancel_url_tpl"), error_url) or error_url
    redirect_url = redirect_url or _fill(cfg.get("redirect_url_tpl"), success_url) or success_url
    first_name, last_name = _split_name(customer_name)
    phone = cstr(phone_number or cfg.get("default_phone") or "251911000000").replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "251" + phone[1:]
    nonce = f"{tx_ref}-{frappe.generate_hash(length=8)}"
    currency = cfg.get("currency") or "ETB"
    payload = {
        "data": {
            "redirect_url": redirect_url,
            "cancel_url": cancel_url,
            "success_url": success_url,
            "error_url": error_url,
            "order_reason": description or f"Payment {tx_ref}",
            "currency": currency,
            "email": customer_email or "orders@ethiobiz.et",
            "first_name": first_name,
            "last_name": last_name,
            "nonce": nonce,
            "order_detail": {
                "amount": amount_val,
                "description": description or f"EthioBiz payment {tx_ref}",
            },
            "phone_number": phone,
            "session_expired": cstr(cfg.get("session_expired") or "5000"),
            "total_amount": str(int(round(amount_val))) if amount_val == int(amount_val) else str(amount_val),
            "tx_ref": tx_ref,
        },
        "message": message or cfg.get("checkout_message") or "EthioBiz checkout",
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Auth": cfg["api_key"],
    }
    url = cfg["base_url"] + cfg.get("create_order_path", CREATE_ORDER_PATH)
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
    except Exception as e:
        frappe.logger("bizmarketing").error(f"AddisPay connection error: {e}")
        frappe.throw(f"Could not connect to AddisPay: {e}")

    if response.status_code not in (200, 201):
        frappe.logger("bizmarketing").error(f"AddisPay create-order failed: {response.status_code} {response.text}")
        frappe.throw(f"Payment initiation failed: {response.text[:400]}")

    try:
        data = response.json()
    except Exception:
        frappe.throw("AddisPay returned a non-JSON response")

    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    checkout_url = data.get("checkout_url") or nested.get("checkout_url") or ""
    uuid = data.get("uuid") or nested.get("uuid") or data.get("order_uuid") or ""
    redirect = ""
    if checkout_url and uuid:
        redirect = f"{checkout_url.rstrip('/')}/{uuid}"
    elif checkout_url:
        redirect = checkout_url
    return {
        "raw": data,
        "checkout_url": checkout_url,
        "uuid": uuid,
        "redirect": redirect,
        "nonce": nonce,
        "tx_ref": tx_ref,
        "sandbox": cfg["sandbox"],
    }


def initiate_payment(subscription_name, amount, customer_email, customer_name):
    """DOBiz SaaS wrapper — tx_ref prefix DOBIZ-."""
    tx_ref = f"DOBIZ-{subscription_name}-{frappe.generate_hash(length=6)}"
    site = get_url()
    result = create_hosted_order(
        amount=amount,
        tx_ref=tx_ref,
        customer_email=customer_email,
        customer_name=customer_name,
        description=f"DOBiz subscription {subscription_name}",
        success_url=f"{site}/dobiz-payment?ref={subscription_name}&status=success",
        error_url=f"{site}/dobiz-payment?ref={subscription_name}&status=failed",
        message="DOBiz subscription payment",
    )
    result["transaction_id"] = result.get("uuid") or tx_ref
    return result


@frappe.whitelist()
def test_connection():
    """Desk button: Magala Checkout Settings → Test AddisPay Connection."""
    if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
        if "Accounts Manager" not in frappe.get_roles() and "Sales Manager" not in frappe.get_roles():
            frappe.throw("Not permitted")
    cfg = get_addispay_config()
    if not cfg.get("api_key"):
        return {"ok": False, "message": "No AddisPay API key. Set it in Magala Checkout Settings or DOBiz SaaS Settings."}
    tx_ref = f"MAGALA-TEST-{frappe.generate_hash(length=6)}"
    try:
        result = create_hosted_order(
            amount=10,
            tx_ref=tx_ref,
            customer_email="test@ethiobiz.et",
            customer_name="AddisPay Test",
            description="Desk connection test (10 ETB UAT)",
            message=cfg.get("checkout_message") or "connection test",
        )
        return {
            "ok": True,
            "message": f"Create-order succeeded. sandbox={cfg['sandbox']} base={cfg['base_url']} uuid={result.get('uuid') or '-'} redirect={result.get('redirect') or '-'}",
            "redirect": result.get("redirect"),
            "uuid": result.get("uuid"),
        }
    except Exception as e:
        return {"ok": False, "message": cstr(e)[:500]}


def initiate_shop_payment(tx_ref, amount, customer_email, customer_name, phone_number=None, description=None):
    """Magala cart wrapper — tx_ref should start with MAGALA-."""
    site = get_url()
    return create_hosted_order(
        amount=amount,
        tx_ref=tx_ref,
        customer_email=customer_email,
        customer_name=customer_name,
        phone_number=phone_number,
        description=description or f"Magala order {tx_ref}",
        success_url=f"{site}/magala-payment-success?tx_ref={tx_ref}",
        error_url=f"{site}/magala-payment-failed?tx_ref={tx_ref}",
        message="Magala marketplace payment",
    )


def verify_payment(transaction_id):
    """Best-effort status check. AddisPay hosted checkout is primarily callback-driven."""
    cfg = _require_api_key()
    headers = {"Accept": "application/json", "Auth": cfg["api_key"]}
    candidates = [
        f"{cfg['base_url']}/checkout-api/v1/get-order/{transaction_id}",
        f"{cfg['base_url']}/checkout-api/v1/orders/{transaction_id}",
        f"{cfg['base_url']}/api/v1/transactions/{transaction_id}",
    ]
    for url in candidates:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            frappe.logger("bizmarketing").error(f"AddisPay verify error {url}: {e}")
    return None


def _payload_status(data):
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    return cstr(data.get("status") or data.get("payment_status") or nested.get("status")).lower()


def _payload_ref(data):
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    return (
        data.get("tx_ref")
        or data.get("reference")
        or data.get("nonce")
        or nested.get("tx_ref")
        or nested.get("reference")
        or ""
    )


def _payload_uuid(data):
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    return data.get("uuid") or data.get("transaction_id") or nested.get("uuid") or ""


def _verify_signature(secret):
    if not secret:
        frappe.logger("bizmarketing").warning("AddisPay webhook secret not configured — signature check skipped")
        return True
    received = frappe.get_request_header("X-AddisPay-Signature") or frappe.get_request_header("Auth")
    if not received:
        frappe.throw("Missing AddisPay signature header")
    payload_str = frappe.request.get_data(as_text=True) or ""
    expected = frappe.utils.sha256_hash(payload_str + secret)
    if received != expected:
        frappe.logger("bizmarketing").error(f"AddisPay signature mismatch: received={received[:20]}... expected={expected[:20]}...")
        frappe.throw("Invalid AddisPay signature")
    return True


@frappe.whitelist(allow_guest=True)
def handle_webhook():
    data = frappe.local.form_dict or {}
    try:
        raw = frappe.request.get_data(as_text=True)
        if raw:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                data = {**parsed, **data}
                if isinstance(parsed.get("data"), dict):
                    data = {**parsed.get("data"), **data}
    except Exception:
        pass

    cfg = get_addispay_config()
    _verify_signature(cfg.get("webhook_secret"))

    tx_ref = _payload_ref(data)
    uuid = _payload_uuid(data)
    status = _payload_status(data)
    transaction_id = uuid or data.get("transaction_id") or tx_ref

    if tx_ref.startswith("MAGALA-") or frappe.db.exists("Magala Shop Payment", {"tx_ref": tx_ref}):
        return _handle_magala_webhook(tx_ref, transaction_id, status)

    if not transaction_id and not tx_ref:
        frappe.throw("Missing required webhook parameters")

    return _handle_dobiz_webhook(tx_ref, transaction_id, status)


def _handle_magala_webhook(tx_ref, transaction_id, status):
    from bismillah_ethiobiz.magala_checkout import mark_addispay_success, mark_addispay_failed

    success_states = ("completed", "success", "successful", "paid", "complete")
    failed_states = ("failed", "fail", "cancelled", "canceled", "error")
    if not status:
        frappe.logger("bizmarketing").warning(f"AddisPay webhook for {tx_ref} has empty status — ignoring (never auto-approve)")
        return {"status": "ignored", "message": "Empty status in webhook — awaiting verified callback"}
    if status in failed_states:
        mark_addispay_failed(tx_ref, transaction_id)
        return {"status": "failed", "message": "Payment failed"}
    if status in success_states:
        mark_addispay_success(tx_ref, transaction_id)
        return {"status": "success", "message": "Magala payment processed"}
    return {"status": "ignored", "message": f"Unknown status: {status}"}


def _handle_dobiz_webhook(subscription_or_ref, transaction_id, status):
    from bizmarketing.api.dobiz_manual_activation import online_auto_activation_enabled

    success_states = ("completed", "success", "successful", "paid", "complete")
    failed_states = ("failed", "fail", "cancelled", "canceled", "error")
    payment_txns = []
    if transaction_id:
        payment_txns = frappe.get_all(
            "DOBiz Payment Transaction",
            filters={"addispay_transaction_id": transaction_id},
            limit=1,
        )
    if not payment_txns and subscription_or_ref:
        payment_txns = frappe.get_all(
            "DOBiz Payment Transaction",
            filters={"subscription": subscription_or_ref.replace("DOBIZ-", "").rsplit("-", 1)[0]},
            limit=1,
        )

    if status in failed_states:
        if payment_txns:
            txn = frappe.get_doc("DOBiz Payment Transaction", payment_txns[0].name)
            txn.db_set("status", "Failed")
            frappe.db.commit()
        return {"status": "failed", "message": "Payment failed"}

    if status not in success_states:
        return {"status": "ignored", "message": f"Unknown status: {status}"}

    if not payment_txns:
        frappe.db.commit()
        return {"status": "success", "message": "No matching DOBiz payment"}

    txn = frappe.get_doc("DOBiz Payment Transaction", payment_txns[0].name)
    txn.db_set("status", "Completed")
    txn.db_set("payment_date", now_datetime())

    if not online_auto_activation_enabled():
        txn.db_set("payment_status", "Pending")
        frappe.db.commit()
        return {"status": "success", "message": "Payment received — queued for manual verification"}

    subscription_name = txn.subscription
    if subscription_name and frappe.db.exists("Subscription", subscription_name):
        sub = frappe.get_doc("Subscription", subscription_name)
        sub.db_set("status", "Active")
        trial_signups = frappe.get_all(
            "DOBiz Trial Signup",
            filters={"company_name": sub.party},
            fields=["name", "email", "full_name"],
        )
        if trial_signups:
            signup = trial_signups[0]
            frappe.db.set_value("DOBiz Trial Signup", signup.name, "status", "Converted")
            from bizmarketing.api.subscription_notifications import send_conversion_email
            plan_name = sub.plans[0].plan if sub.plans else "DOBiz Standard Plan"
            send_conversion_email(signup.email, signup.full_name, plan_name)

    frappe.db.commit()
    return {"status": "success", "message": "Payment processed"}
