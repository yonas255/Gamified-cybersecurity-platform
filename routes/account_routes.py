# importing required libraries for encoding
import base64
import io
import pyotp
import qrcode # QR code generation
from flask import Blueprint, render_template, request, redirect, url_for, flash # authentication logic
from flask_login import login_required, current_user # flask routing
from models import db # database library
from models.user import User # user models

# creating a blueprint for account-related routes with a URL prefix for organization.
account_bp = Blueprint("account", __name__, url_prefix="/account")

# define the route to set up 2FA, generates a secret if not already created
# builds a QR code for authenticator apps, and renders the setup page with requred data.
@account_bp.route("/2fa", methods=["GET", "POST"])
@login_required
def twofa():
    user = db.session.get(User, current_user.id)

    # Generating secret if missing
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
    # labeling in authenticator apps
    label = f"{issuer}:{user.email}"
    totp = pyotp.TOTP(user.totp_secret)
    otpauth_url = totp.provisioning_uri(name=label, issuer_name=issuer)

    # making the QR image (base64) to show in HTML
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

# handles the verification of the 2FA code entered by the user, checks validity using TOTP
# enables 2FA if the code is valid
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

# providing the functionallity to disable 2FA by removing the secret
# updating the users setting in the database
@account_bp.route("/2fa/disable", methods=["POST"])
@login_required
def disable_2fa():
    user = db.session.get(User, current_user.id)
    user.totp_enabled = False
    user.totp_secret = None
    db.session.commit()
    flash("2FA has been disabled.")
    return redirect(url_for("account.twofa"))
