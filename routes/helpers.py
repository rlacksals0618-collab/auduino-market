from functools import wraps

from flask import flash, redirect, request, session, url_for
from postgrest.exceptions import APIError


def login_required(view):
    """로그인한 사람만 들어올 수 있는 페이지에 붙입니다."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("로그인이 필요합니다.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    """관리자만 들어올 수 있는 페이지에 붙입니다."""
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("관리자만 이용할 수 있습니다.", "error")
            return redirect(url_for("products.index"))
        return view(*args, **kwargs)
    return wrapper


def error_message(e):
    """Supabase 오류에서 사람이 읽을 수 있는 메시지만 꺼냅니다."""
    if isinstance(e, APIError) and e.message:
        return e.message
    return str(e)


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
