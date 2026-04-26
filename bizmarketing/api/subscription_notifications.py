"""
BISMALLAH — Subscription Email Notifications
All trial lifecycle emails sent from onboard@ethiobiz.et.

Uses frappe.sendmail() directly to avoid company_global_filter issues.
"""
import frappe


SENDER = "onboard@ethiobiz.et"
SENDER_NAME = "DOBiz by EthioBiz"


def send_welcome_email(email, full_name, company_name):
    """Welcome email sent immediately after trial signup."""
    subject = f"Bismillah! Welcome to DOBiz, {full_name}! Your 7-Day Trial is Active"
    message = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🌟 Welcome to DOBiz Smart ERP</h1>
            <p style="color: #bbdefb; margin-top: 8px;">Your 7-Day Free Trial Has Begun</p>
        </div>
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Alhamdulillah! Your free trial for <strong>{company_name}</strong> is now active on DOBiz Smart ERP.</p>

            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #2e7d32;">✅ What's Included in Your Trial:</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Core ERP Modules (CRM, HR, Accounting, Inventory)</li>
                    <li>Hadeeda AI Chat Assistant (50 messages/day)</li>
                    <li>1 Social Media Account via BizMarketing</li>
                    <li>Standard Email Support</li>
                </ul>
            </div>

            <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><strong>⏰ Trial Duration:</strong> 7 days from today</p>
                <p style="margin: 5px 0 0 0;">After the trial, you can upgrade to our Standard (ETB 3,000/mo) or Premium (ETB 7,500/mo) plan.</p>
            </div>

            <p style="text-align: center; margin: 25px 0;">
                <a href="https://ethiobiz.et/app" style="background: #1a73e8; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">🚀 Start Using DOBiz Now</a>
            </p>
            <p style="color: #666; font-size: 13px;">Need help? Reply to this email or chat with Hadeeda at ethiobiz.et</p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 0 0 12px 12px; text-align: center; font-size: 12px; color: #999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>
    """

    try:
        frappe.sendmail(
            recipients=[email],
            sender=SENDER,
            subject=subject,
            message=message,
            now=True,
        )
        frappe.logger("bizmarketing").info(f"Welcome email sent to {email}")
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send welcome email to {email}: {e}")


def send_expiry_warning_email(email, company_name, days_remaining, expiry_date):
    """Warning email sent 3 days and 1 day before trial expiry."""
    urgency = "⚠️" if days_remaining == 3 else "🚨"
    subject = f"{urgency} Your DOBiz Trial Expires in {days_remaining} Day{'s' if days_remaining > 1 else ''}!"
    message = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #ff9800, #e65100); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px;">{urgency} Trial Expiring Soon</h1>
            <p style="color: #ffe0b2; margin-top: 8px;">{days_remaining} day{'s' if days_remaining > 1 else ''} remaining</p>
        </div>
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
            <p>Assalamu Alaikum,</p>
            <p>Your DOBiz trial for <strong>{company_name}</strong> will expire on <strong>{expiry_date}</strong>.</p>
            <p>Don't lose access to your business data and AI-powered tools! Upgrade now to continue:</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #e3f2fd;">
                    <td style="padding: 12px; border: 1px solid #ddd;"><strong>Standard Plan</strong></td>
                    <td style="padding: 12px; border: 1px solid #ddd;">ETB 3,000/month</td>
                    <td style="padding: 12px; border: 1px solid #ddd;">Core ERP + Hadeeda Chat</td>
                </tr>
                <tr style="background: #fff3e0;">
                    <td style="padding: 12px; border: 1px solid #ddd;"><strong>Premium Plan</strong></td>
                    <td style="padding: 12px; border: 1px solid #ddd;">ETB 7,500/month</td>
                    <td style="padding: 12px; border: 1px solid #ddd;">Everything + Full Hadeeda AI + BizFlow</td>
                </tr>
            </table>

            <p style="text-align: center; margin: 25px 0;">
                <a href="https://ethiobiz.et/app" style="background: #e65100; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">Upgrade Now →</a>
            </p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 0 0 12px 12px; text-align: center; font-size: 12px; color: #999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>
    """

    try:
        frappe.sendmail(
            recipients=[email],
            sender=SENDER,
            subject=subject,
            message=message,
            now=True,
        )
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send warning email to {email}: {e}")


def send_expired_email(email, company_name):
    """Email sent when trial has expired and access is revoked."""
    subject = "Your DOBiz Trial Has Expired — Subscribe to Continue"
    message = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #c62828, #b71c1c); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px;">Trial Period Ended</h1>
            <p style="color: #ffcdd2; margin-top: 8px;">Your access has been temporarily paused</p>
        </div>
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
            <p>Assalamu Alaikum,</p>
            <p>Your 7-day DOBiz trial for <strong>{company_name}</strong> has ended.</p>
            <p>Your data is safe and preserved. Subscribe to instantly restore full access:</p>

            <p style="text-align: center; margin: 25px 0;">
                <a href="https://ethiobiz.et/app" style="background: #1a73e8; color: white; padding: 14px 35px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px;">Subscribe Now — Starting ETB 3,000/mo</a>
            </p>

            <p style="color: #666;">Questions? Contact us at <a href="mailto:onboard@ethiobiz.et">onboard@ethiobiz.et</a></p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 0 0 12px 12px; text-align: center; font-size: 12px; color: #999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>
    """

    try:
        frappe.sendmail(
            recipients=[email],
            sender=SENDER,
            subject=subject,
            message=message,
            now=True,
        )
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send expired email to {email}: {e}")


def send_conversion_email(email, full_name, plan_name):
    """Confirmation email after upgrading from trial to paid."""
    subject = f"Alhamdulillah! Welcome to {plan_name}, {full_name}!"
    message = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2e7d32, #1b5e20); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🎉 Subscription Activated!</h1>
            <p style="color: #c8e6c9; margin-top: 8px;">{plan_name}</p>
        </div>
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
            <p>Assalamu Alaikum <strong>{full_name}</strong>,</p>
            <p>Alhamdulillah! Your <strong>{plan_name}</strong> subscription is now active. Full access has been restored.</p>

            <p style="text-align: center; margin: 25px 0;">
                <a href="https://ethiobiz.et/app" style="background: #2e7d32; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">Go to DOBiz Dashboard →</a>
            </p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 0 0 12px 12px; text-align: center; font-size: 12px; color: #999;">
            <p>Biz Technology Solutions · Addis Ababa, Ethiopia</p>
        </div>
    </div>
    """

    try:
        frappe.sendmail(
            recipients=[email],
            sender=SENDER,
            subject=subject,
            message=message,
            now=True,
        )
    except Exception as e:
        frappe.logger("bizmarketing").error(f"Failed to send conversion email to {email}: {e}")
