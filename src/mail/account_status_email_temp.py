import os
from datetime import datetime


def account_status_email_temp(data: dict) -> str:
    image = os.environ.get("EMAIL_TEMP_IMAGE")
    year = datetime.now().year
    name = data.get("name", "User")
    action = data.get("action", "STATUS_CHANGE").upper()
    reason = data.get("reason", "No specific reason provided.")
    expires_at = data.get("expiresAt")

    status_titles = {
        "BAN": "Account Banned",
        "SUSPEND": "Account Suspended",
        "UNAPPROVE": "Account Access Revoked",
        "UNBAN": "Account Re-activated",
        "ACTIVE": "Account Restored",
    }

    badge_colors = {
        "BAN": {"bg": "#fee2e2", "border": "#fecaca", "text": "#dc2626"},
        "SUSPEND": {"bg": "#fef3c7", "border": "#fde68a", "text": "#d97706"},
        "UNAPPROVE": {"bg": "#fee2e2", "border": "#fecaca", "text": "#dc2626"},
        "UNBAN": {"bg": "#dcfce7", "border": "#bbf7d0", "text": "#16a34a"},
        "ACTIVE": {"bg": "#dcfce7", "border": "#bbf7d0", "text": "#16a34a"},
    }

    title = status_titles.get(action, f"Account Status: {action}")
    badge = badge_colors.get(
        action, {"bg": "#e0e7ff", "border": "#c7d2fe", "text": "#4f46e5"}
    )

    expiry_row = ""
    if expires_at:
        expiry_row = f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #6366f1; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
          <p style="margin: 0; color: #475569; font-size: 14px;">
            <strong>Duration / Suspension Expiry:</strong> {expires_at}
          </p>
        </div>
        """

    is_restriction = action in ("BAN", "SUSPEND", "UNAPPROVE")

    appeal_section = (
        """
        <p style="color: #6b7280; font-size: 14px; margin-top: 24px; line-height: 1.5;">
          If you believe this action was taken in error or would like to submit an appeal, please reply directly to this email or contact our support team.
        </p>
        """
        if is_restriction
        else """
        <p style="color: #6b7280; font-size: 14px; margin-top: 24px; line-height: 1.5;">
          You can now log back into your account and resume using all platform features.
        </p>
        """
    )

    logo_markup = (
        f'<div class="logo"><img src="{image}" alt="Logo" class="logo-img"></div>'
        if image
        else ""
    )

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: #f3f4f6;
        margin: 0;
        padding: 0;
      }}
      .container {{
        max-width: 580px;
        margin: 40px auto;
        background-color: #ffffff;
        padding: 36px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
      }}
      .logo {{
        text-align: center;
        margin-bottom: 24px;
      }}
      .logo-img {{
        max-width: 140px;
      }}
      .badge {{
        background-color: {badge["bg"]};
        border: 1px solid {badge["border"]};
        color: {badge["text"]};
        padding: 6px 14px;
        border-radius: 16px;
        display: inline-block;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 16px;
      }}
      h1 {{
        color: #111827;
        font-size: 22px;
        font-weight: 700;
        margin: 0 0 16px 0;
      }}
      p {{
        color: #374151;
        line-height: 1.6;
        font-size: 15px;
        margin: 0 0 16px 0;
      }}
      .reason-box {{
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin: 20px 0;
      }}
      .reason-label {{
        color: #6b7280;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }}
      .reason-text {{
        color: #1f2937;
        font-size: 14px;
        margin: 0;
      }}
      .footer {{
        text-align: center;
        font-size: 12px;
        color: #9ca3af;
        margin-top: 32px;
        border-top: 1px solid #f3f4f6;
        padding-top: 20px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      {logo_markup}
      <div>
        <span class="badge">{title}</span>
      </div>
      <h1>Hello {name},</h1>
      <p>
        This is an official administrative notice regarding your account status on our platform.
      </p>

      <div class="reason-box">
        <div class="reason-label">Administrative Note / Reason</div>
        <p class="reason-text">{reason}</p>
      </div>

      {expiry_row}
      {appeal_section}

      <div class="footer">
        <p style="margin: 0;">&copy; {year} All rights reserved.</p>
      </div>
    </div>
  </body>
</html>"""
