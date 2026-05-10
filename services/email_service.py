# Premium Email Service — AEIOU AI
# Embeds the actual SVG logo inline (email-safe static version).
# Each email type has its own distinct visual identity.
import secrets
import logging
from typing import Optional
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_verification_code() -> str:
    """Generate a high-entropy 6-digit verification code."""
    return str(secrets.randbelow(900000) + 100000)


def get_email_branding():
    """Returns consistent branding assets for all premium emails."""
    return {
        "app_name": "AEIOU AI",
        "tagline": "Business Intelligence, Elevated",
        "primary_color": "#4F46E5",       # Indigo 600
        "primary_dark": "#3730A3",         # Indigo 800
        "accent_color": "#8B5CF6",         # Violet 500
        "bg_light": "#F8FAFC",             # Slate 50
        "bg_card": "#FFFFFF",
        "text_dark": "#0F172A",            # Slate 900
        "text_muted": "#64748B",           # Slate 500
        "border_color": "#E2E8F0",         # Slate 200
        "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", "AEIOU AI <support@aeiou.ai>"),
        "website": getattr(settings, "FRONTEND_URL", "https://aeiou.ai"),
    }


# ─── AEIOU AI SVG Logo (inline, email-safe static version) ──────────────────
# This is a static (no-animation) version of the animated bar logo for email
# compatibility. Email clients strip <animate> tags.
LOGO_SVG = """
<table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
  <tr>
    <td align="center" style="padding-bottom:4px;">
      <!-- AEIOU AI Bar Logo (static, email-safe) -->
      <svg width="52" height="52" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"
           style="display:block;margin:0 auto;">
        <circle cx="50" cy="50" r="48" fill="#EEF2FF"/>
        <rect x="20" y="45" width="8" height="35" rx="4" fill="#3B82F6"/>
        <rect x="35" y="30" width="8" height="50" rx="4" fill="#6366F1"/>
        <rect x="50" y="20" width="8" height="60" rx="4" fill="#8B5CF6"/>
        <rect x="65" y="35" width="8" height="45" rx="4" fill="#6366F1"/>
        <rect x="80" y="50" width="8" height="30" rx="4" fill="#3B82F6"/>
      </svg>
    </td>
  </tr>
  <tr>
    <td align="center" style="padding-top:6px;">
      <span style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                   font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-0.5px;">
        AEIOU <span style="color:#4F46E5;">AI</span>
      </span>
    </td>
  </tr>
</table>
"""


def _email_wrapper(branding: dict, inner_html: str, preview_text: str = "", accent: str = "") -> str:
    """
    Shared high-fidelity email wrapper.
    accent: optional hex color to tint the top header stripe.
    """
    stripe_color = accent or branding["primary_color"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{branding['app_name']}</title>
</head>
<body style="margin:0;padding:0;background-color:{branding['bg_light']};
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
             -webkit-font-smoothing:antialiased;mso-line-height-rule:exactly;">

  <!-- Preview text (hidden) -->
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;
              font-size:1px;line-height:1px;color:{branding['bg_light']};">
    {preview_text}&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌
  </div>

  <!-- Outer wrapper -->
  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
         style="background-color:{branding['bg_light']};">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <!-- Card -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0"
               style="width:100%;max-width:560px;background-color:{branding['bg_card']};
                      border-radius:20px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.06),0 1px 4px rgba(0,0,0,0.04);">

          <!-- Top accent stripe -->
          <tr>
            <td style="height:4px;background:linear-gradient(90deg,{stripe_color},{branding['accent_color']});"></td>
          </tr>

          <!-- Logo header -->
          <tr>
            <td align="center" style="padding:40px 40px 24px;">
              {LOGO_SVG}
            </td>
          </tr>

          <!-- Main content -->
          {inner_html}

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <div style="height:1px;background-color:{branding['border_color']};"></div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:28px 40px;text-align:center;">
              <p style="margin:0 0 12px;font-size:13px;color:{branding['text_muted']};line-height:20px;">
                &copy; 2025 {branding['app_name']}. All rights reserved.
              </p>
              <p style="margin:0;font-size:12px;color:#94A3B8;">
                <a href="{branding['website']}" style="color:{branding['primary_color']};text-decoration:none;font-weight:600;">Website</a>
                <span style="margin:0 8px;color:#CBD5E1;">&bull;</span>
                <a href="mailto:{branding['support_email']}" style="color:{branding['primary_color']};text-decoration:none;font-weight:600;">Support</a>
                <span style="margin:0 8px;color:#CBD5E1;">&bull;</span>
                <a href="{branding['website']}/privacy" style="color:{branding['primary_color']};text-decoration:none;font-weight:600;">Privacy</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _render_otp_block(code: str, color: str = "#4F46E5") -> str:
    """Renders a visually distinct OTP code display block."""
    digits = "  ".join(list(code))
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
        <td align="center" style="padding:8px 0 24px;">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0">
            <tr>
              <td align="center"
                  style="background-color:#F1F5F9;border:2px solid {color}22;
                         border-radius:14px;padding:28px 40px;">
                <span style="display:block;font-size:11px;font-weight:700;
                             color:{color};text-transform:uppercase;
                             letter-spacing:3px;margin-bottom:14px;">
                  Verification Code
                </span>
                <span style="font-family:'Courier New',Courier,monospace;
                             font-size:42px;font-weight:900;
                             letter-spacing:10px;color:{color};
                             line-height:1;">
                  {code}
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>"""


def _send_email(subject: str, text_body: str, html_body: str, to_email: str, from_email: str) -> bool:
    """Low-level send with structured error logging."""
    try:
        msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("✅ Email sent | to=%s | subject=%s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("❌ Email failed | to=%s | subject=%s | error=%s", to_email, subject, exc, exc_info=True)
        return False


# ─── Email: Verify Email ─────────────────────────────────────────────────────

def send_verification_email(email: str, username: str, code: str) -> bool:
    """Send a premium email verification code with the AEIOU AI logo."""
    try:
        branding = get_email_branding()
        inner = f"""
        <tr>
          <td style="padding:0 40px 36px;">
            <h1 style="margin:0 0 14px;font-size:26px;font-weight:800;
                       color:{branding['text_dark']};letter-spacing:-0.5px;text-align:center;">
              Verify your email
            </h1>
            <p style="margin:0 0 28px;font-size:15px;line-height:26px;
                      color:{branding['text_muted']};text-align:center;">
              Hi <strong>{username}</strong>, welcome to {branding['app_name']}!<br>
              Use the code below to verify your email address and activate your account.
            </p>

            {_render_otp_block(code, branding['primary_color'])}

            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td align="center"
                    style="background-color:#EEF2FF;border-radius:10px;padding:14px 20px;">
                  <p style="margin:0;font-size:13px;color:#4338CA;font-weight:600;">
                    ⏱ This code expires in <strong>15 minutes</strong>
                  </p>
                </td>
              </tr>
            </table>

            <p style="margin:20px 0 0;font-size:12px;color:#94A3B8;text-align:center;line-height:18px;">
              If you didn't create an account, you can safely ignore this email.
            </p>
          </td>
        </tr>"""

        html = _email_wrapper(branding, inner,
                              f"Your AEIOU AI verification code is {code}",
                              branding["primary_color"])
        text = (f"Welcome to {branding['app_name']}, {username}!\n\n"
                f"Your email verification code is: {code}\n\n"
                f"This code expires in 15 minutes.\n\n"
                f"If you didn't create an account, ignore this email.")

        return _send_email(
            f"Verify your email — {branding['app_name']}",
            text, html, email, branding["support_email"]
        )
    except Exception as e:
        logger.error("Failed to build verification email: %s", e, exc_info=True)
        return False


# ─── Email: Password Reset ───────────────────────────────────────────────────

def send_password_reset_email(email: str, username: str, code: str) -> bool:
    """Send a premium password reset email."""
    try:
        branding = get_email_branding()
        inner = f"""
        <tr>
          <td style="padding:0 40px 36px;">
            <h1 style="margin:0 0 14px;font-size:26px;font-weight:800;
                       color:{branding['text_dark']};letter-spacing:-0.5px;text-align:center;">
              Reset your password
            </h1>
            <p style="margin:0 0 28px;font-size:15px;line-height:26px;
                      color:{branding['text_muted']};text-align:center;">
              Hi <strong>{username}</strong>, we received a request to reset your<br>
              {branding['app_name']} account password. Use the code below.
            </p>

            {_render_otp_block(code, "#D97706")}

            <!-- Security warning -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                   style="margin-bottom:20px;">
              <tr>
                <td style="background-color:#FFFBEB;border:1px solid #FDE68A;
                           border-radius:10px;padding:16px 20px;">
                  <p style="margin:0;font-size:13px;color:#92400E;line-height:20px;text-align:center;">
                    <strong>🔒 Security notice:</strong> If you didn't request this,
                    please <a href="{branding['website']}/login"
                              style="color:#D97706;font-weight:700;">secure your account</a> immediately.
                  </p>
                </td>
              </tr>
            </table>

            <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;line-height:18px;">
              This code expires in <strong>15 minutes</strong>.
            </p>
          </td>
        </tr>"""

        html = _email_wrapper(branding, inner,
                              f"Your AEIOU AI password reset code is {code}",
                              "#D97706")
        text = (f"Hi {username},\n\n"
                f"Reset your {branding['app_name']} password using this code: {code}\n\n"
                f"This code expires in 15 minutes.\n\n"
                f"If you didn't request this, please change your password immediately.")

        return _send_email(
            f"Reset your password — {branding['app_name']}",
            text, html, email, branding["support_email"]
        )
    except Exception as e:
        logger.error("Failed to build password reset email: %s", e, exc_info=True)
        return False


# ─── Email: Welcome (post-verification) ─────────────────────────────────────

def send_welcome_email(email: str, username: str) -> bool:
    """Send a high-fidelity welcome email after account verification."""
    try:
        branding = get_email_branding()
        inner = f"""
        <tr>
          <td style="padding:0 40px 36px;">
            <!-- Hero emoji -->
            <p style="margin:0 0 20px;font-size:48px;text-align:center;line-height:1;">🎉</p>
            <h1 style="margin:0 0 14px;font-size:28px;font-weight:800;
                       color:{branding['text_dark']};letter-spacing:-0.5px;text-align:center;">
              Welcome to {branding['app_name']}!
            </h1>
            <p style="margin:0 0 32px;font-size:16px;line-height:28px;
                      color:{branding['text_muted']};text-align:center;">
              Hey <strong>{username}</strong>, your account is verified and ready.<br>
              You now have full access to your AI business intelligence platform.
            </p>

            <!-- CTA Button -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center"
                   style="margin:0 auto 32px;">
              <tr>
                <td align="center"
                    style="border-radius:12px;
                           background:linear-gradient(135deg,{branding['primary_color']},{branding['accent_color']});">
                  <a href="{branding['website']}/dashboard"
                     style="display:inline-block;padding:16px 36px;font-size:15px;
                            font-weight:700;color:#ffffff;text-decoration:none;
                            letter-spacing:0.3px;border-radius:12px;">
                    Open Your Dashboard &rarr;
                  </a>
                </td>
              </tr>
            </table>

            <!-- Feature tiles -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td style="padding:6px 4px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                         style="background-color:#F8FAFC;border-radius:12px;padding:16px;">
                    <tr>
                      <td style="font-size:20px;width:36px;">🤖</td>
                      <td style="padding-left:12px;font-size:14px;color:{branding['text_dark']};">
                        <strong>AI Chat</strong> — Ask questions, get strategic insights instantly.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:6px 4px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                         style="background-color:#F8FAFC;border-radius:12px;padding:16px;">
                    <tr>
                      <td style="font-size:20px;width:36px;">📋</td>
                      <td style="padding-left:12px;font-size:14px;color:{branding['text_dark']};">
                        <strong>Task Manager</strong> — Organize work with AI-powered suggestions.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:6px 4px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                         style="background-color:#F8FAFC;border-radius:12px;padding:16px;">
                    <tr>
                      <td style="font-size:20px;width:36px;">📄</td>
                      <td style="padding-left:12px;font-size:14px;color:{branding['text_dark']};">
                        <strong>Documents</strong> — Upload docs and ask AI anything about them.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

        html = _email_wrapper(branding, inner,
                              f"Welcome {username}! Your AEIOU AI account is ready.",
                              branding["primary_color"])
        text = (f"Hi {username},\n\n"
                f"Welcome to {branding['app_name']}! Your account is fully verified.\n\n"
                f"Visit your dashboard: {branding['website']}/dashboard\n\n"
                f"Features available:\n"
                f"• AI Chat — Strategic business insights\n"
                f"• Task Manager — Organize & prioritize work\n"
                f"• Documents — Upload and query your files\n\n"
                f"Questions? Reply to this email.")

        return _send_email(
            f"Welcome to {branding['app_name']}! 🎉",
            text, html, email, branding["support_email"]
        )
    except Exception as e:
        logger.error("Failed to build welcome email: %s", e, exc_info=True)
        return False


# ─── Email: New Login Alert ──────────────────────────────────────────────────

def send_login_alert_email(email: str, username: str, ip_address: str, device: str) -> bool:
    """Premium security alert for new logins."""
    try:
        branding = get_email_branding()

        # Truncate very long user-agent strings for readability
        device_display = device[:80] + "..." if len(device) > 80 else device

        inner = f"""
        <tr>
          <td style="padding:0 40px 36px;">
            <!-- Shield icon -->
            <p style="margin:0 0 16px;font-size:40px;text-align:center;line-height:1;">🔐</p>
            <h1 style="margin:0 0 14px;font-size:24px;font-weight:800;
                       color:{branding['text_dark']};letter-spacing:-0.5px;text-align:center;">
              New login detected
            </h1>
            <p style="margin:0 0 28px;font-size:15px;line-height:26px;
                      color:{branding['text_muted']};text-align:center;">
              Hi <strong>{username}</strong>, a new sign-in was detected on your<br>
              {branding['app_name']} account. Review the details below.
            </p>

            <!-- Login details card -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                   style="background-color:#F8FAFC;border:1px solid #E2E8F0;
                          border-radius:14px;margin-bottom:24px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                      <td style="padding-bottom:12px;border-bottom:1px solid #E2E8F0;
                                 padding-bottom:12px;">
                        <p style="margin:0;font-size:11px;font-weight:700;color:#94A3B8;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                          IP Address
                        </p>
                        <p style="margin:0;font-size:15px;font-weight:700;color:{branding['text_dark']};
                                  font-family:'Courier New',Courier,monospace;">
                          {ip_address}
                        </p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding-top:12px;">
                        <p style="margin:0;font-size:11px;font-weight:700;color:#94A3B8;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                          Device / Browser
                        </p>
                        <p style="margin:0;font-size:14px;color:{branding['text_dark']};
                                  word-break:break-all;line-height:20px;">
                          {device_display}
                        </p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <!-- Action prompt -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td style="background-color:#FEF2F2;border:1px solid #FECACA;
                           border-radius:10px;padding:16px 20px;text-align:center;">
                  <p style="margin:0;font-size:13px;color:#991B1B;line-height:20px;">
                    <strong>Not you?</strong> &nbsp;
                    <a href="{branding['website']}/forgot-password"
                       style="color:#DC2626;font-weight:700;text-decoration:underline;">
                      Secure your account now
                    </a>
                  </p>
                </td>
              </tr>
            </table>

            <p style="margin:20px 0 0;font-size:12px;color:#94A3B8;text-align:center;">
              If this was you, no action is needed. This is an automated security notification.
            </p>
          </td>
        </tr>"""

        html = _email_wrapper(branding, inner,
                              f"New login to your AEIOU AI account from {ip_address}",
                              "#DC2626")
        text = (f"Hi {username},\n\n"
                f"A new login was detected on your {branding['app_name']} account.\n\n"
                f"IP Address: {ip_address}\n"
                f"Device: {device}\n\n"
                f"If this wasn't you, secure your account immediately:\n"
                f"{branding['website']}/forgot-password")

        return _send_email(
            f"Security Alert: New login detected — {branding['app_name']}",
            text, html, email, branding["support_email"]
        )
    except Exception as e:
        logger.error("Failed to build login alert email: %s", e, exc_info=True)
        return False
