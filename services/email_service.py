"""
Premium Email Service for AEIOU AI
Handles transactional emails with professional branding.
"""
import os
import random
from typing import Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return str(random.randint(100000, 999999))


def get_email_branding():
    """Get consistent email branding."""
    return {
        "app_name": "AEIOU AI",
        "logo_url": f"{settings.FRONTEND_URL}/logos/app-logo.svg" if hasattr(settings, 'FRONTEND_URL') else "",
        "primary_color": "#3B82F6",
        "secondary_color": "#1E40AF",
        "support_email": settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "support@aeiou.ai",
        "website": settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://aeiou.ai",
    }


def send_verification_email(email: str, username: str, code: str) -> bool:
    """Send email verification code with premium branding."""
    try:
        branding = get_email_branding()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - {branding['app_name']}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .header {{ background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%); padding: 48px 40px; text-align: center; }}
        .header img {{ width: 64px; height: 64px; margin-bottom: 16px; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; font-weight: 700; }}
        .content {{ padding: 48px 40px; }}
        .greeting {{ font-size: 18px; color: #1e293b; margin-bottom: 24px; font-weight: 600; }}
        .message {{ color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 32px; }}
        .code-container {{ background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 32px; text-align: center; margin: 32px 0; border: 2px dashed #3B82F6; }}
        .code-label {{ color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
        .code {{ font-size: 42px; font-weight: 700; color: #1e40af; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
        .expiry {{ color: #94a3b8; font-size: 14px; margin-top: 24px; text-align: center; }}
        .footer {{ background: #f8fafc; padding: 32px 40px; text-align: center; border-top: 1px solid #e2e8f0; }}
        .footer-text {{ color: #94a3b8; font-size: 14px; margin: 0; }}
        .social-links {{ margin-top: 16px; }}
        .social-links a {{ color: #64748b; text-decoration: none; margin: 0 12px; font-size: 14px; }}
    </style>
</head>
<body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 40px 20px;">
                <div class="container">
                    <div class="header">
                        <h1>🔐 Verify Your Email</h1>
                    </div>
                    <div class="content">
                        <p class="greeting">Hi {username},</p>
                        <p class="message">
                            Welcome to <strong>{branding['app_name']}</strong>! To complete your registration and secure your account, 
                            please enter the verification code below. This ensures that you have access to this email address.
                        </p>
                        <div class="code-container">
                            <div class="code-label">Your Verification Code</div>
                            <div class="code">{code}</div>
                        </div>
                        <p class="expiry">
                            ⏰ This code expires in <strong>15 minutes</strong> for security reasons.
                        </p>
                    </div>
                    <div class="footer">
                        <p class="footer-text">
                            Didn't request this? You can safely ignore this email.<br>
                            Need help? Contact us at <a href="mailto:{branding['support_email']}" style="color: #3B82F6;">{branding['support_email']}</a>
                        </p>
                        <div class="social-links">
                            <a href="{branding['website']}">Website</a>
                        </div>
                        <p style="color: #cbd5e1; font-size: 12px; margin-top: 24px;">
                            © 2024 {branding['app_name']}. All rights reserved.
                        </p>
                    </div>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_content = f"""
Hi {username},

Welcome to {branding['app_name']}! 

Your verification code is: {code}

This code expires in 15 minutes.

If you didn't request this, please ignore this email.

Need help? Contact: {branding['support_email']}

© 2024 {branding['app_name']}
"""
        
        email_msg = EmailMultiAlternatives(
            subject=f"🔐 Verify Your Email - {branding['app_name']}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "noreply@aeiou.ai",
            to=[email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(email: str, username: str, code: str) -> bool:
    """Send password reset code with premium branding."""
    try:
        branding = get_email_branding()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password - {branding['app_name']}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 48px 40px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; font-weight: 700; }}
        .content {{ padding: 48px 40px; }}
        .greeting {{ font-size: 18px; color: #1e293b; margin-bottom: 24px; font-weight: 600; }}
        .message {{ color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 32px; }}
        .code-container {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-radius: 12px; padding: 32px; text-align: center; margin: 32px 0; border: 2px dashed #f59e0b; }}
        .code-label {{ color: #92400e; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
        .code {{ font-size: 42px; font-weight: 700; color: #92400e; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
        .expiry {{ color: #94a3b8; font-size: 14px; margin-top: 24px; text-align: center; }}
        .warning {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px 20px; margin-top: 24px; border-radius: 8px; }}
        .warning-text {{ color: #991b1b; font-size: 14px; margin: 0; }}
        .footer {{ background: #f8fafc; padding: 32px 40px; text-align: center; border-top: 1px solid #e2e8f0; }}
        .footer-text {{ color: #94a3b8; font-size: 14px; margin: 0; }}
    </style>
</head>
<body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 40px 20px;">
                <div class="container">
                    <div class="header">
                        <h1>🔑 Reset Your Password</h1>
                    </div>
                    <div class="content">
                        <p class="greeting">Hi {username},</p>
                        <p class="message">
                            We received a request to reset your password for your <strong>{branding['app_name']}</strong> account. 
                            Use the code below to set a new password. If you didn't request this, please ignore this email.
                        </p>
                        <div class="code-container">
                            <div class="code-label">Password Reset Code</div>
                            <div class="code">{code}</div>
                        </div>
                        <p class="expiry">
                            ⏰ This code expires in <strong>15 minutes</strong> for security reasons.
                        </p>
                        <div class="warning">
                            <p class="warning-text">
                                ⚠️ Never share this code with anyone. Our team will never ask for it.
                            </p>
                        </div>
                    </div>
                    <div class="footer">
                        <p class="footer-text">
                            Need help? Contact us at <a href="mailto:{branding['support_email']}" style="color: #3B82F6;">{branding['support_email']}</a>
                        </p>
                        <p style="color: #cbd5e1; font-size: 12px; margin-top: 24px;">
                            © 2024 {branding['app_name']}. All rights reserved.
                        </p>
                    </div>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_content = f"""
Hi {username},

We received a request to reset your password for your {branding['app_name']} account.

Your password reset code is: {code}

This code expires in 15 minutes.

⚠️ Never share this code with anyone. Our team will never ask for it.

If you didn't request this, please ignore this email.

Need help? Contact: {branding['support_email']}

© 2024 {branding['app_name']}
"""
        
        email_msg = EmailMultiAlternatives(
            subject=f"🔑 Reset Your Password - {branding['app_name']}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "noreply@aeiou.ai",
            to=[email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_welcome_email(email: str, username: str) -> bool:
    """Send welcome email after verification."""
    try:
        branding = get_email_branding()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to {branding['app_name']}!</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background: #f8fafc; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 48px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 32px; }}
        .content {{ padding: 48px; }}
        .greeting {{ font-size: 20px; color: #1e293b; margin-bottom: 16px; }}
        .message {{ color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 32px; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%); color: white; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-weight: 600; }}
        .features {{ margin: 32px 0; }}
        .feature {{ display: flex; align-items: center; margin: 16px 0; }}
        .feature-icon {{ font-size: 24px; margin-right: 16px; }}
        .feature-text {{ color: #334155; font-size: 15px; }}
    </style>
</head>
<body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr><td style="padding: 40px 20px;">
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to AEIOU AI!</h1>
                </div>
                <div class="content">
                    <p class="greeting">Hi {username},</p>
                    <p class="message">
                        Your email has been verified! You're now part of the AEIOU AI community. 
                        Get ready to supercharge your business with AI-powered insights.
                    </p>
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="{branding['website']}/chat" class="cta-button">Start Chatting →</a>
                    </div>
                    <div class="features">
                        <div class="feature">
                            <span class="feature-icon">💬</span>
                            <span class="feature-text">AI-powered business assistant</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📊</span>
                            <span class="feature-text">Smart analytics & insights</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📄</span>
                            <span class="feature-text">Document analysis & summaries</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">✅</span>
                            <span class="feature-text">Task management & tracking</span>
                        </div>
                    </div>
                </div>
            </div>
        </td></tr>
    </table>
</body>
</html>
"""
        
        email_msg = EmailMultiAlternatives(
            subject=f"🎉 Welcome to {branding['app_name']}!",
            body=f"""
Hi {username},

Welcome to {branding['app_name']}! Your email has been verified.

Get started: {branding['website']}/chat

© 2024 {branding['app_name']}
""",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "noreply@aeiou.ai",
            to=[email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False
