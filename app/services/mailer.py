"""Email sender + secure token helpers.

Backends (set MAIL_BACKEND env var):
  - "brevo"   -> Brevo HTTP API (recommended for Render — uses port 443)
  - "smtp"    -> Standard SMTP (Gmail etc — blocked on Render free tier!)
  - "console" -> Prints to terminal (default, dev only)
"""
import smtplib
import ssl
import requests
from email.message import EmailMessage
from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


def _serializer(salt):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=salt)


def make_token(value, salt="generic"):
    return _serializer(salt).dumps(value)


def read_token(token, salt="generic", max_age=3600):
    try:
        return _serializer(salt).loads(token, max_age=max_age)
    except SignatureExpired:
        return None
    except BadSignature:
        return None


def _build_message(to_email, subject, text, html):
    msg = EmailMessage()
    from_name = current_app.config.get("MAIL_FROM_NAME", "Aether AI")
    from_addr = (current_app.config.get("MAIL_FROM")
                 or current_app.config.get("MAIL_USERNAME")
                 or "noreply@aether.local")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _send_console(to, subject, text):
    print("\n" + "=" * 70, flush=True)
    print(f"📧  [CONSOLE EMAIL]  To: {to}", flush=True)
    print(f"    Subject: {subject}", flush=True)
    print("-" * 70, flush=True)
    print(text, flush=True)
    print("=" * 70 + "\n", flush=True)


def _send_smtp(to, subject, text, html):
    cfg = current_app.config
    server = cfg["MAIL_SERVER"]
    port = int(cfg["MAIL_PORT"])
    timeout = 10
    context = ssl.create_default_context()
    msg = _build_message(to, subject, text, html)
    use_ssl = cfg.get("MAIL_USE_SSL", False) or port == 465
    if use_ssl:
        with smtplib.SMTP_SSL(server, port, context=context, timeout=timeout) as smtp:
            if cfg.get("MAIL_USERNAME") and cfg.get("MAIL_PASSWORD"):
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(server, port, timeout=timeout) as smtp:
            if cfg.get("MAIL_USE_TLS"):
                smtp.starttls(context=context)
            if cfg.get("MAIL_USERNAME") and cfg.get("MAIL_PASSWORD"):
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            smtp.send_message(msg)


def _send_brevo(to, subject, text, html):
    cfg = current_app.config
    api_key = cfg.get("BREVO_API_KEY", "")
    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not set")
    from_name = cfg.get("MAIL_FROM_NAME", "Aether AI")
    from_email = cfg.get("MAIL_FROM") or cfg.get("MAIL_USERNAME") or "noreply@aether.local"
    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": api_key,
            "content-type": "application/json",
            "accept": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Brevo HTTP {resp.status_code}: {resp.text}")


def send_email(to_email, subject, text, html):
    backend = (current_app.config.get("MAIL_BACKEND") or "console").lower()
    print("=" * 70, flush=True)
    print(f"📧 send_email() called", flush=True)
    print(f"   To: {to_email}", flush=True)
    print(f"   Subject: {subject}", flush=True)
    print(f"   Backend: '{backend}'", flush=True)
    print("=" * 70, flush=True)
    try:
        if backend == "brevo":
            print("→ Attempting Brevo HTTP send...", flush=True)
            _send_brevo(to_email, subject, text, html)
            print(f"✓ BREVO SUCCESS: email sent to {to_email}", flush=True)
        elif backend == "smtp" and current_app.config.get("MAIL_USERNAME"):
            print("→ Attempting SMTP send...", flush=True)
            _send_smtp(to_email, subject, text, html)
            print(f"✓ SMTP SUCCESS: email sent to {to_email}", flush=True)
        else:
            print("→ Using console fallback", flush=True)
            _send_console(to_email, subject, text)
    except Exception as e:
        print(f"✗ {backend.upper()} FAILED: {type(e).__name__}: {e}", flush=True)
        _send_console(to_email, subject, text)


def send_verification_email(user):
    token = make_token(user.email, salt="verify-email")
    link = url_for("auth.verify_email", token=token, _external=True)
    ctx = {"user": user, "link": link, "brand": "Aether AI"}
    send_email(
        user.email,
        "Verify your Aether AI email",
        render_template("emails/verify.txt", **ctx),
        render_template("emails/verify.html", **ctx),
    )


def send_reset_email(user):
    token = make_token(user.email, salt="password-reset")
    link = url_for("auth.reset_password", token=token, _external=True)
    ctx = {"user": user, "link": link, "brand": "Aether AI"}
    send_email(
        user.email,
        "Reset your Aether AI password",
        render_template("emails/reset.txt", **ctx),
        render_template("emails/reset.html", **ctx),
    )