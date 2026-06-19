"""Email sender + secure token helpers."""
import smtplib
import ssl
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


def _send_console(msg):
    print("\n" + "=" * 70)
    print(f"📧  [CONSOLE EMAIL]  To: {msg['To']}")
    print(f"    Subject: {msg['Subject']}")
    print("-" * 70)
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print(part.get_content())
            break
    print("=" * 70 + "\n")


def _send_smtp(msg):
    cfg = current_app.config
    server = cfg["MAIL_SERVER"]
    port = int(cfg["MAIL_PORT"])
    timeout = 10  # never hang more than 10 seconds
    context = ssl.create_default_context()

    # Use SSL (port 465) or STARTTLS (port 587) based on config
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


def send_email(to_email, subject, text, html):
    msg = _build_message(to_email, subject, text, html)
    backend = (current_app.config.get("MAIL_BACKEND") or "console").lower()
    username = current_app.config.get("MAIL_USERNAME", "")
    password_len = len(current_app.config.get("MAIL_PASSWORD", ""))

    # DEBUG: print exactly what config we're using
    print("=" * 70, flush=True)
    print(f"📧 send_email() called", flush=True)
    print(f"   To: {to_email}", flush=True)
    print(f"   Subject: {subject}", flush=True)
    print(f"   MAIL_BACKEND: '{backend}'", flush=True)
    print(f"   MAIL_USERNAME: '{username}'", flush=True)
    print(f"   MAIL_PASSWORD length: {password_len}", flush=True)
    print(f"   MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}", flush=True)
    print(f"   MAIL_PORT: {current_app.config.get('MAIL_PORT')}", flush=True)
    print("=" * 70, flush=True)

    try:
        if backend == "smtp" and username:
            print("→ Attempting SMTP send...", flush=True)
            _send_smtp(msg)
            print(f"✓ SMTP SUCCESS: email sent to {to_email}", flush=True)
        else:
            print(f"→ Using console fallback (backend={backend}, username={'set' if username else 'EMPTY'})", flush=True)
            _send_console(msg)
    except Exception as e:
        print(f"✗ SMTP FAILED: {type(e).__name__}: {e}", flush=True)
        _send_console(msg)


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