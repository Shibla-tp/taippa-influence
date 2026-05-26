import smtplib
import urllib.request
import urllib.parse
import urllib.error
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
SMTP_HOST  = "smtp.gmail.com"
SMTP_PORT  = 587
SMTP_USER  = "shibla@taippa.com"
SMTP_PASS  = "hnvm oxbs pufr hobm"   # Gmail App Password

FROM_NAME  = "Shibla @ TAIPPA Influence"
FROM_EMAIL = "shibla@taippa.com"
SUBJECT    = "We made it free."


AIRTABLE_TABLE   = "influencer_outreach"

# Airtable field names
FIELD_EMAIL      = "email_id"       # recipient email
FIELD_CONTACT    = "contact_person" # recipient name
FIELD_EMAIL_BODY = "email_1"        # stores sent HTML content
FIELD_STATUS     = "status"         # updated to "sent"


# ─────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>TAIPPA Influence — We made it free.</title>
<style>
  body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
  table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
  img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
  body {{ margin: 0; padding: 0; background-color: #FFFFFF; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
  .email-wrapper {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; padding: 0; }}
  .email-card {{ background: #FFFFFF; border-radius: 0; overflow: hidden; }}
  .header {{ background: #111827; padding: 24px 40px; }}
  .logo-text {{ color: white; font-size: 15px; font-weight: 600; letter-spacing: 0.01em; }}
  .logo-sub {{ color: rgba(255,255,255,0.4); font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-top: 1px; }}
  .body {{ padding: 40px; }}
  .greeting {{ font-size: 15px; color: #6B7280; margin: 0 0 24px; }}
  .hook {{ font-size: 15px; color: #111827; line-height: 1.75; margin: 0 0 8px; }}
  .hook-q {{ font-size: 15px; color: #374151; line-height: 1.75; margin: 0 0 4px; padding-left: 16px; font-style: italic; }}
  .answer {{ font-size: 16px; font-weight: 600; color: #111827; margin: 20px 0; line-height: 1.75; }}
  .divider {{ border: none; border-top: 1px solid #F3F4F6; margin: 28px 0; }}
  .tools-label {{ font-size: 11px; font-weight: 700; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 16px; }}
  .tool-name {{ font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 3px; }}
  .tool-desc {{ font-size: 13px; color: #6B7280; margin: 0; line-height: 1.5; }}
  .tool-time {{ font-size: 11px; font-weight: 700; color: #FF6B6B; margin: 4px 0 0; }}
  @media only screen and (max-width: 480px) {{
    .header {{ padding: 20px 20px !important; }}
    .body {{ padding: 24px 20px !important; }}
    .footer {{ padding: 20px !important; }}
    .optout {{ padding: 16px 20px 24px !important; }}
    .creators-box {{ padding: 14px 16px !important; }}
    .creators-stat {{ font-size: 22px !important; }}
    .cta-btn {{ padding: 13px 20px !important; font-size: 14px !important; display: block !important; text-align: center !important; width: 100% !important; box-sizing: border-box !important; }}
  }}
  .creators-box {{ background: #F9FAFB; border-radius: 12px; padding: 18px 20px; margin: 24px 0; }}
  .creators-stat {{ font-size: 28px; font-weight: 700; color: #111827; margin: 0 0 4px; }}
  .creators-label {{ font-size: 13px; color: #6B7280; margin: 0 0 12px; }}
  .tag {{ font-size: 11px; font-weight: 500; color: #374151; background: #F3F4F6; padding: 4px 10px; border-radius: 20px; display: inline-block; margin: 3px 3px 0 0; }}
  .verdict {{ font-size: 15px; color: #111827; line-height: 1.75; margin: 20px 0; }}
  .verdict-highlight {{ color: #FF6B6B; font-weight: 700; }}
  .cta-wrap {{ text-align: center; margin: 32px 0 8px; }}
  .cta-note {{ text-align: center; font-size: 12px; color: #9CA3AF; margin: 10px 0 0; }}
  .footer {{ background: #F9FAFB; padding: 24px 40px; border-top: 1px solid #F3F4F6; }}
  .footer-name {{ font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 2px; }}
  .footer-role {{ font-size: 13px; color: #6B7280; margin: 0 0 4px; }}
  .footer-email {{ font-size: 13px; color: #FF6B6B; text-decoration: none; display: block; margin: 0 0 2px; }}
  .footer-url {{ font-size: 13px; color: #6B7280; margin: 0; }}
  .optout {{ text-align: center; padding: 20px 40px 28px; }}
  .optout p {{ font-size: 11px; color: #9CA3AF; line-height: 1.6; margin: 0 0 8px; }}
  .unsub-btn {{ display: inline-block; font-size: 11px; color: #9CA3AF; text-decoration: none; border: 1px solid #E5E7EB; border-radius: 20px; padding: 5px 16px; }}
</style>
</head>
<body>
<div class="email-wrapper">
<div class="email-card">

  <div class="header">
    <table cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td valign="middle" style="padding-right:14px;">
          <img src="http://taippa.com/wp-content/uploads/2025/01/cropped-Untitled_design__4_-removebg-preview-1-1-e1737533076395.png"
               width="44" height="40" alt="TAIPPA" style="display:block;width:44px;height:40px;">
        </td>
        <td valign="middle">
          <span class="logo-text">TAIPPA Influence</span>
          <span class="logo-sub">AI Influencer Marketing · GCC</span>
        </td>
      </tr>
    </table>
  </div>

  <div class="body">
    <p class="greeting">Hi {name},</p>
    <p class="hook">Most brands in the GCC pay an agency AED 20,000+ just to answer three questions:</p>
    <p class="hook-q">Which creators should we use?</p>
    <p class="hook-q">What should the campaign look like?</p>
    <p class="hook-q">How much should we spend?</p>
    <p class="answer">We answer all three for free. In under 5 minutes. With AI.</p>
    <hr class="divider">
    <p class="tools-label">What you get at app.taippa.com — free, no sign-up</p>

    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid #F9FAFB;">
      <tr>
        <td width="40" valign="top" style="padding:14px 0 14px 0;width:40px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr><td width="26" height="26" style="width:26px;height:26px;background:#FFF0F0;border-radius:6px;color:#FF6B6B;font-size:12px;font-weight:700;text-align:center;line-height:26px;font-family:Helvetica,Arial,sans-serif;">1</td></tr></table>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;">
          <p class="tool-name">Market Entry Intelligence</p>
          <p class="tool-desc">Consumer behaviour, competitor landscape, legal requirements and market size for any GCC market.</p>
          <p class="tool-time"><a href="https://app.taippa.com/tools/market-entry" style="color:#FF6B6B;text-decoration:none;font-size:11px;font-weight:700;">Try now →</a></p>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid #F9FAFB;">
      <tr>
        <td width="40" valign="top" style="padding:14px 0 14px 0;width:40px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr><td width="26" height="26" style="width:26px;height:26px;background:#FFF0F0;border-radius:6px;color:#FF6B6B;font-size:12px;font-weight:700;text-align:center;line-height:26px;font-family:Helvetica,Arial,sans-serif;">2</td></tr></table>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;">
          <p class="tool-name">Campaign Strategy Generator</p>
          <p class="tool-desc">Input your brief. Get a full influencer campaign strategy built for the GCC.</p>
          <p class="tool-time"><a href="https://app.taippa.com/" style="color:#FF6B6B;text-decoration:none;font-size:11px;font-weight:700;">Try now →</a></p>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid #F9FAFB;">
      <tr>
        <td width="40" valign="top" style="padding:14px 0 14px 0;width:40px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr><td width="26" height="26" style="width:26px;height:26px;background:#FFF0F0;border-radius:6px;color:#FF6B6B;font-size:12px;font-weight:700;text-align:center;line-height:26px;font-family:Helvetica,Arial,sans-serif;">3</td></tr></table>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;">
          <p class="tool-name">Competitor Influencer Analysis</p>
          <p class="tool-desc">See exactly which creators your competitors are using and what is working for them.</p>
          <p class="tool-time"><a href="https://app.taippa.com/tools/competitor-research" style="color:#FF6B6B;text-decoration:none;font-size:11px;font-weight:700;">Try now →</a></p>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid #F9FAFB;">
      <tr>
        <td width="40" valign="top" style="padding:14px 0 14px 0;width:40px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr><td width="26" height="26" style="width:26px;height:26px;background:#FFF0F0;border-radius:6px;color:#FF6B6B;font-size:12px;font-weight:700;text-align:center;line-height:26px;font-family:Helvetica,Arial,sans-serif;">4</td></tr></table>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;">
          <p class="tool-name">Influencer Budget Calculator</p>
          <p class="tool-desc">Know exactly what to spend across creator tiers before you commit a single dirham.</p>
          <p class="tool-time"><a href="https://app.taippa.com/tools/budget-calculator" style="color:#FF6B6B;text-decoration:none;font-size:11px;font-weight:700;">Try now →</a></p>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td width="40" valign="top" style="padding:14px 0 14px 0;width:40px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr><td width="26" height="26" style="width:26px;height:26px;background:#FFF0F0;border-radius:6px;color:#FF6B6B;font-size:12px;font-weight:700;text-align:center;line-height:26px;font-family:Helvetica,Arial,sans-serif;">5</td></tr></table>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;">
          <p class="tool-name">Platform Strategy</p>
          <p class="tool-desc">Instagram vs TikTok vs Snapchat vs YouTube — broken down by GCC country.</p>
          <p class="tool-time"><a href="https://app.taippa.com/tools/platform-strategy" style="color:#FF6B6B;text-decoration:none;font-size:11px;font-weight:700;">Try now →</a></p>
        </td>
      </tr>
    </table>

    <hr class="divider">
    <div class="creators-box">
      <p class="creators-stat">1,621</p>
      <p class="creators-label">Verified GCC creators across 17 categories</p>
      <div>
        <span class="tag">UAE</span>
        <span class="tag">KSA</span>
        <span class="tag">Bahrain</span>
        <span class="tag">Qatar</span>
        <span class="tag">Oman</span>
        <span class="tag">Kuwait</span>
      </div>
    </div>
    <p class="verdict">Browse, match and activate creators directly — no agency, no middleman, no markup.</p>
    <p class="verdict">This is what agencies charge <span class="verdict-highlight">AED 20,000+</span> for. It's free.</p>
    <div class="cta-wrap">
      <a href="https://app.taippa.com" class="cta-btn" style="display:inline-block;background:#FF6B6B;color:#FFFFFF !important;text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;border-radius:10px;letter-spacing:0.01em;text-align:center;">Try it free — app.taippa.com</a>
    </div>
    <p class="cta-note">No sign-up required &nbsp;·&nbsp; No credit card &nbsp;·&nbsp; Takes 3 minutes</p>
  </div>

  <div class="footer">
    <p class="footer-name">Shibla</p>
    <p class="footer-role">TAIPPA Influence</p>
    <a href="mailto:shibla@taippa.com" class="footer-email">shibla@taippa.com</a>
    <p class="footer-url">app.taippa.com</p>
  </div>

  <div class="optout">
    <p>You received this because we think TAIPPA could be useful for your brand.<br>
    If you'd prefer not to hear from us, no hard feelings.</p>
    <a href="https://app.taippa.com/unsubscribe" class="unsub-btn">Unsubscribe</a>
  </div>

</div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────
# AIRTABLE: get first pending record (email_1 empty)
# ─────────────────────────────────────────────
def get_one_pending_record():
    """Return the first record where email_1 is empty. Returns dict or None."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type":  "application/json",
    }
    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/"
        f"{urllib.parse.quote(AIRTABLE_TABLE)}"
    )
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise Exception(f"Airtable fetch failed: {e.read().decode()}")

    for rec in data.get("records", []):
        fields = rec.get("fields", {})

        # Only process if email_1 is empty/missing
        if fields.get(FIELD_EMAIL_BODY, "").strip():
            continue

        email   = fields.get(FIELD_EMAIL, "").strip()
        contact = fields.get(FIELD_CONTACT, "").strip()

        if email:
            return {
                "id":      rec["id"],
                "email":   email,
                "contact": contact or "there",
            }

    return None  # no pending records


# ─────────────────────────────────────────────
# AIRTABLE: mark record as sent
# ─────────────────────────────────────────────
def mark_record_sent(record_id: str, html_body: str) -> None:
    """Write HTML into email_1 and set status = 'sent'."""
    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/"
        f"{urllib.parse.quote(AIRTABLE_TABLE)}/{record_id}"
    )
    payload = json.dumps({
        "fields": {
            FIELD_EMAIL_BODY: html_body,
            FIELD_STATUS:     "sent",
        }
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type":  "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        raise Exception(f"Airtable update failed: {e.read().decode()}")


# ─────────────────────────────────────────────
# SEND ONE EMAIL
# ─────────────────────────────────────────────
def send_one_email(to_email: str, to_name: str) -> str:
    """Send email and return rendered HTML body."""
    html_body = HTML_TEMPLATE.format(name=to_name)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"]      = to_email

    plain = (
        f"Hi {to_name},\n\n"
        "Most brands in the GCC pay an agency AED 20,000+ just to answer three questions.\n"
        "We answer all three for free. In under 5 minutes. With AI.\n\n"
        "Try it free: https://app.taippa.com\n\n"
        "— Shibla, TAIPPA Influence\n"
        "shibla@taippa.com"
    )

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())

    return html_body


# ─────────────────────────────────────────────
# MAIN ENTRY POINT  (called by Flask route)
# ─────────────────────────────────────────────
def process_brand_outreach_email():
    """
    Finds the first pending record (email_1 empty),
    sends one email, updates Airtable.
    Returns a result dict suitable for jsonify().
    """
    try:
        record = get_one_pending_record()
    except Exception as e:
        return {"status": "error", "message": f"Airtable fetch failed: {str(e)}"}

    if not record:
        return {"status": "success", "message": "No pending records found"}

    to_email  = record["email"]
    to_name   = record["contact"]
    record_id = record["id"]

    try:
        html_body = send_one_email(to_email, to_name)
    except Exception as e:
        return {"status": "error", "message": f"Email send failed to {to_email}: {str(e)}"}

    try:
        mark_record_sent(record_id, html_body)
    except Exception as e:
        # Email sent but Airtable update failed — log it but don't fail silently
        return {
            "status":  "partial",
            "message": f"Email sent to {to_email} but Airtable update failed: {str(e)}",
        }

    return {
        "status":    "success",
        "message":   f"Email sent to {to_name} <{to_email}> and Airtable updated",
        "record_id": record_id,
    }