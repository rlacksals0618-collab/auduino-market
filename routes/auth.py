from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from routes.helpers import error_message
from supabase_client import db, new_auth_client

auth_bp = Blueprint("auth", __name__)


def save_login(user_id, email):
    """로그인한 사람의 정보를 세션(쿠키)에 저장합니다."""
    found = db.table("profiles").select("*").eq("id", user_id).execute().data
    profile = found[0] if found else {"name": email.split("@")[0], "is_admin": False}
    session.clear()
    session["user_id"] = user_id
    session["email"] = email
    session["name"] = profile["name"]
    session["is_admin"] = profile["is_admin"]


def safe_next(default):
    """로그인 후 돌아갈 주소 (우리 사이트 안의 주소만 허용)"""
    target = request.args.get("next", "")
    if target.startswith("/") and not target.startswith("//"):
        return target
    return default


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email:
            flash("이름과 이메일을 입력하세요.", "error")
        elif len(password) < 6:
            flash("비밀번호는 6자 이상이어야 합니다.", "error")
        else:
            try:
                # 수업용이라 이메일 인증 없이 바로 가입 완료 처리
                user = db.auth.admin.create_user(
                    {"email": email, "password": password, "email_confirm": True}
                ).user
                db.table("profiles").insert({"id": user.id, "email": email, "name": name}).execute()
                save_login(user.id, email)
                flash(f"{name}님, 가입을 환영합니다!")
                return redirect(url_for("products.index"))
            except Exception as e:
                message = error_message(e)
                if "already" in message:
                    message = "이미 가입된 이메일입니다."
                flash(f"회원가입 실패: {message}", "error")

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        try:
            result = new_auth_client().auth.sign_in_with_password({"email": email, "password": password})
            save_login(result.user.id, email)
            flash(f"{session['name']}님, 반갑습니다!")
            return redirect(safe_next(url_for("products.index")))
        except Exception:
            flash("이메일 또는 비밀번호가 올바르지 않습니다.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("로그아웃했습니다.")
    return redirect(url_for("products.index"))
