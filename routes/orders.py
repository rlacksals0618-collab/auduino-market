from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from routes.cart import get_cart_items
from routes.helpers import error_message, login_required
from supabase_client import db

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, total = get_cart_items(session["user_id"])
    if not items:
        flash("장바구니가 비어 있습니다.", "error")
        return redirect(url_for("cart.view"))

    if request.method == "POST":
        recipient = request.form.get("recipient", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not (recipient and phone and address):
            flash("받는 분, 연락처, 주소를 모두 입력하세요.", "error")
        else:
            try:
                # 재고 확인 + 주문 생성 + 재고 차감 + 장바구니 비우기 (DB 함수가 한 번에 처리)
                order_id = db.rpc("place_order", {
                    "p_user_id": session["user_id"],
                    "p_recipient": recipient,
                    "p_phone": phone,
                    "p_address": address,
                }).execute().data
                flash(f"주문이 완료되었습니다. (주문번호 {order_id})")
                return redirect(url_for("orders.my_orders"))
            except Exception as e:
                flash(f"주문 실패: {error_message(e)}", "error")

    return render_template("checkout.html", items=items, total=total)


@orders_bp.route("/orders")
@login_required
def my_orders():
    orders = (
        db.table("orders").select("*, order_items(*)")
        .eq("user_id", session["user_id"])
        .order("id", desc=True)
        .execute().data
    )
    return render_template("orders.html", orders=orders)
