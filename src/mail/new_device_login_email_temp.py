import os
from datetime import datetime


def new_device_login_email_temp(data: dict) -> str:
    image = os.environ.get("EMAIL_TEMP_IMAGE")
    year = datetime.now().year
    name = data.get("name", "User")
    device = data.get("device", "Unknown Device")
    ip = data.get("ip", "Unknown IP")
    login_time = data.get("time", "Just now")

    return f"""
  <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: 'Verdana', 'Arial', sans-serif;
          background-color: #f2f3f8;
          margin: 0;
          padding: 0;
        }}
        .container {{
          max-width: 600px;
          margin: 40px auto;
          background-color: #ffffff;
          padding: 40px;
          border-radius: 12px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        }}
        .logo {{
          text-align: center;
          margin-bottom: 24px;
        }}
        .logo-img {{
          max-width: 140px;
        }}
        .alert-badge {{
          background-color: #fee2e2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 8px 16px;
          border-radius: 20px;
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
          color: #4b5563;
          line-height: 1.6;
          font-size: 15px;
          margin-bottom: 16px;
        }}
        .device-card {{
          background-color: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 18px 24px;
          margin: 24px 0;
        }}
        .detail-row {{
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #f3f4f6;
          font-size: 14px;
        }}
        .detail-row:last-child {{
          border-bottom: none;
        }}
        .detail-label {{
          color: #6b7280;
          font-weight: 500;
        }}
        .detail-value {{
          color: #111827;
          font-weight: 600;
        }}
        .warning-box {{
          background-color: #fffbeb;
          border-left: 4px solid #f59e0b;
          padding: 14px 18px;
          margin: 20px 0;
          font-size: 13px;
          color: #92400e;
          border-radius: 0 6px 6px 0;
        }}
        .footer {{
          margin-top: 32px;
          font-size: 12px;
          color: #9ca3af;
          text-align: center;
          border-top: 1px solid #e5e7eb;
          padding-top: 20px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">
          {f'<img class="logo-img" src="{image}" alt="Logo" />' if image else '<h2 style="color:#b26a7b;margin:0;">Mount Fuji</h2>'}
        </div>
        <div style="text-align: center;">
          <span class="alert-badge">🛡️ Security Notice</span>
          <h1>New Device Sign-in Detected</h1>
        </div>
        <p>Hello <strong>{name}</strong>,</p>
        <p>Your account was recently accessed from a new device or browser. Below are the details of this sign-in:</p>
        
        <div class="device-card">
          <div class="detail-row">
            <span class="detail-label">Device & Browser:</span>
            <span class="detail-value">{device}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">IP Address:</span>
            <span class="detail-value">{ip}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Timestamp:</span>
            <span class="detail-value">{login_time}</span>
          </div>
        </div>

        <div class="warning-box">
          <strong>Didn't recognize this activity?</strong>
          <br />
          If this wasn't you, your account password may have been compromised. Please immediately reset your password and revoke all active sessions.
        </div>

        <p>If you initiated this sign-in, no further action is required.</p>

        <div class="footer">
          <p>Mount Fuji Backend Security Team • Automated Alert</p>
          <p>© {year} Mount Fuji. All rights reserved.</p>
        </div>
      </div>
    </body>
  </html>
  """
