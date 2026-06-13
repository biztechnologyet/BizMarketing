import frappe
import requests
import json
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def handle_webhook():
    data = frappe.local.form_dict
    settings = frappe.get_single('DOBiz SaaS Settings')
    secret = settings.get_password('addispay_webhook_secret') if settings.addispay_webhook_secret else None
    if not secret:
        frappe.logger('bizmarketing').error('AddisPay webhook secret not configured')
        frappe.throw('AddisPay webhook not configured')

    received_signature = frappe.get_request_header('X-AddisPay-Signature')
    if not received_signature:
        frappe.throw('Missing AddisPay signature header')

    payload_str = frappe.request_data
    expected_signature = frappe.utils.sha256_hash(payload_str + secret)
    if received_signature != expected_signature:
        frappe.throw('Invalid AddisPay signature')

    transaction_id = data.get('transaction_id')
    status = data.get('status')
    subscription_name = data.get('reference')

    if not transaction_id or not subscription_name:
        frappe.throw('Missing required webhook parameters')

    if status == 'completed':
        payment_txns = frappe.get_all(
            'DOBiz Payment Transaction',
            filters={'addispay_transaction_id': transaction_id},
            limit=1
        )
        if payment_txns:
            txn = frappe.get_doc('DOBiz Payment Transaction', payment_txns[0].name)
            txn.db_set('status', 'Completed')
            txn.db_set('payment_date', now_datetime())

            sub = frappe.get_doc('Subscription', subscription_name)
            sub.db_set('status', 'Active')

            trial_signups = frappe.get_all(
                'DOBiz Trial Signup',
                filters={'company_name': sub.party},
                fields=['name', 'email', 'full_name']
            )
            if trial_signups:
                signup = trial_signups[0]
                frappe.db.set_value('DOBiz Trial Signup', signup.name, 'status', 'Converted')
                from bizmarketing.api.subscription_notifications import send_conversion_email
                plan_name = sub.plans[0].plan if sub.plans else 'DOBiz Standard Plan'
                send_conversion_email(signup.email, signup.full_name, plan_name)

        frappe.db.commit()
        return {'status': 'success', 'message': 'Payment processed'}

    elif status == 'failed':
        payment_txns = frappe.get_all(
            'DOBiz Payment Transaction',
            filters={'addispay_transaction_id': transaction_id},
            limit=1
        )
        if payment_txns:
            txn = frappe.get_doc('DOBiz Payment Transaction', payment_txns[0].name)
            txn.db_set('status', 'Failed')
            frappe.db.commit()
        return {'status': 'failed', 'message': 'Payment failed'}

    return {'status': 'ignored', 'message': f'Unknown status: {status}'}


def initiate_payment(subscription_name, amount, customer_email, customer_name):
    settings = frappe.get_single('DOBiz SaaS Settings')
    api_key = settings.get_password('addispay_api_key') if settings.addispay_api_key else None
    if not api_key:
        frappe.throw('AddisPay API key not configured in DOBiz SaaS Settings')

    sandbox = settings.addispay_sandbox_mode
    base_url = 'https://sandbox.addispay.et/api/v1' if sandbox else 'https://api.addispay.et/api/v1'

    payload = {
        'amount': amount,
        'currency': 'ETB',
        'reference': subscription_name,
        'customer_email': customer_email,
        'customer_name': customer_name,
        'callback_url': f'{frappe.utils.get_url()}/api/method/bizmarketing.api.addispay.handle_webhook',
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(f'{base_url}/checkout', json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return response.json()
        else:
            frappe.logger('bizmarketing').error(f'AddisPay checkout failed: {response.text}')
            frappe.throw(f'Payment initiation failed: {response.text}')
    except Exception as e:
        frappe.logger('bizmarketing').error(f'AddisPay connection error: {e}')
        frappe.throw(f'Could not connect to AddisPay: {e}')


def verify_payment(transaction_id):
    settings = frappe.get_single('DOBiz SaaS Settings')
    api_key = settings.get_password('addispay_api_key') if settings.addispay_api_key else None
    if not api_key:
        frappe.throw('AddisPay API key not configured')

    sandbox = settings.addispay_sandbox_mode
    base_url = 'https://sandbox.addispay.et/api/v1' if sandbox else 'https://api.addispay.et/api/v1'

    headers = {
        'Authorization': f'Bearer {api_key}',
    }

    try:
        response = requests.get(f'{base_url}/transactions/{transaction_id}', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            frappe.logger('bizmarketing').error(f'AddisPay verification failed: {response.text}')
            return None
    except Exception as e:
        frappe.logger('bizmarketing').error(f'AddisPay verify error: {e}')
        return None
