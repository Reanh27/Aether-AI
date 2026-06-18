"""Login / Register / Logout + Email verification + Password reset."""
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session)
from flask_login import login_user, logout_user, login_required, current_user
from .. import db
from ..models import User
from ..forms import (RegisterForm, LoginForm,
                     ForgotPasswordForm, ResetPasswordForm)
from ..services.mailer import (make_token, read_token,
                               send_verification_email, send_reset_email)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register"))
        user = User(email=form.email.data.lower(), name=form.name.data,
                    email_verified=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        try:
            send_verification_email(user)
        except Exception:
            pass
        login_user(user)
        flash("Welcome to Aether AI! Check your email to verify your account.",
              "success")
        return redirect(url_for("dashboard.index"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_url = request.args.get("next") or url_for("dashboard.index")
            return redirect(next_url)
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/verify/<token>")
def verify_email(token):
    email = read_token(token, salt="verify-email", max_age=60 * 60 * 24)
    if not email:
        flash("That verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Account not found.", "danger")
        return redirect(url_for("auth.login"))
    if user.email_verified:
        flash("Email already verified — you're all set!", "info")
    else:
        user.email_verified = True
        db.session.commit()
        flash("✓ Email verified! Thank you.", "success")
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
@login_required
def resend_verification():
    if current_user.email_verified:
        flash("Your email is already verified.", "info")
        return redirect(url_for("dashboard.index"))
    last_sent = session.get("verif_last_sent")
    if last_sent:
        last = datetime.fromisoformat(last_sent)
        if datetime.utcnow() - last < timedelta(minutes=1):
            flash("Please wait a minute before requesting another email.",
                  "warning")
            return redirect(request.referrer or url_for("dashboard.index"))
    try:
        send_verification_email(current_user)
        session["verif_last_sent"] = datetime.utcnow().isoformat()
        flash("Verification email sent. Please check your inbox.", "success")
    except Exception as e:
        flash(f"Couldn't send email: {e}", "danger")
    return redirect(request.referrer or url_for("dashboard.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                send_reset_email(user)
            except Exception:
                pass
        flash("If that email is registered, a reset link has been sent.",
              "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = read_token(token, salt="password-reset", max_age=60 * 60)
    if not email:
        flash("That reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Account not found.", "danger")
        return redirect(url_for("auth.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("✓ Password updated. Please log in with your new password.",
              "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form, email=email)