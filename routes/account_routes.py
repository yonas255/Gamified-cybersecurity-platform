import base64
import io
import pyotp
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.user import User

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/2fa", methods=["GET", "POST"])
@login_required
def twofa():
    user = db.session.get(User, current_user.id)

    # Generate secret if missing
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        db.session.commit()

    if user.totp_enabled:
        return render_template(
            "account_2fa.html",
            qr_b64=None,
            secret=None,
            enabled=True,
        )
    issuer = "GamifiedCyberPlatform"
    # label in authenticator apps
    label = f"{issuer}:{user.email}"
    totp = pyotp.TOTP(user.totp_secret)
    otpauth_url = totp.provisioning_uri(name=label, issuer_name=issuer)

    # Make QR image (base64) to show in HTML
    img = qrcode.make(otpauth_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template(
        "account_2fa.html",
        qr_b64=qr_b64,
        secret=user.totp_secret,
        enabled=bool(user.totp_enabled),
    )

@account_bp.route("/2fa/verify", methods=["POST"])
@login_required
def verify_2fa():
    code = request.form.get("code", "").strip()
    user = db.session.get(User, current_user.id)

    if not user.totp_secret:
        flash("2FA not initialized.")
        return redirect(url_for("account.twofa"))
    
    totp = pyotp.TOTP(user.totp_secret)

    if totp.verify(code):
        user.totp_enabled = True
        db.session.commit()
        flash("2FA enabled successfully.")
    else:
        flash("Invalid authentication code.")

    return redirect(url_for("account.twofa"))

@account_bp.route("/2fa/disable", methods=["POST"])
@login_required
def disable_2fa():
    user = db.session.get(User, current_user.id)
    user.totp_enabled = False
    user.totp_secret = None
    db.session.commit()
    flash("2FA has been disabled.")
    return redirect(url_for("account.twofa"))
