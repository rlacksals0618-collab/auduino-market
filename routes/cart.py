from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from routes.helpers import login_required, to_int
from supabase_client import db

cart_bp = Blueprint("cart", __name__)

CART_FIELDS = "id, quantity, products(id, name, price, stock, image_url)"


def get_cart_items(user_id):
    items = db.table("cart_items").select(CART_FIELDS).eq("user_id", user_id).order("id").execute().data
    total = sum(i["quantity"] * i["products"]["price"] for i in items)
    return items, total


@cart_bp.route("/cart")
@login_required
def view():
    items, total = get_cart_items(session["user_id"])
    return render_template("cart.html", items=items, total=total)


@cart_bp.route("/cart/add", methods=["POST"])
@login_required
def add():
    product_id = to_int(request.form.get("product_id"))
    quantity = max(1, to_int(request.form.get("quantity"), 1))

    found = db.table("products").select("id, name, stock").eq("id", product_id).execute().data
    if not found:
        flash("존재하지 않는 상품입니다.", "error")
        return redirect(url_for("products.index"))
    product = found[0]

    existing = (
        db.table("cart_items").select("id, quantity")
        .eq("user_id", session["user_id"]).eq("product_id", product_id)
        .execute().data
    )
    new_quantity = quantity + (existing[0]["quantity"] if existing else 0)

    if new_quantity > product["stock"]:
        flash(f"재고가 부족합니다. (남은 수량 {product['stock']}개)", "error")
        return redirect(url_for("products.detail", product_id=product_id))

    if existing:
        db.table("cart_items").update({"quantity": new_quantity}).eq("id", existing[0]["id"]).execute()
    else:
        db.table("cart_items").insert(
            {"user_id": session["user_id"], "product_id": product_id, "quantity": quantity}
        ).execute()

    flash(f"'{product['name']}'을(를) 장바구니에 담았습니다.")
    if request.form.get("buy_now"):
        return redirect(url_for("orders.checkout"))
    return redirect(url_for("cart.view"))


@cart_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update(item_id):
    quantity = to_int(request.form.get("quantity"), 1)
    found = (
        db.table("cart_items").select("id, products(stock)")
        .eq("id", item_id).eq("user_id", session["user_id"])
        .execute().data
    )
    if found:
        stock = found[0]["products"]["stock"]
        if quantity < 1:
            db.table("cart_items").delete().eq("id", item_id).execute()
        elif quantity > stock:
            flash(f"재고가 부족합니다. (남은 수량 {stock}개)", "error")
        else:
            db.table("cart_items").update({"quantity": quantity}).eq("id", item_id).execute()
    return redirect(url_for("cart.view"))


@cart_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove(item_id):
    db.table("cart_items").delete().eq("id", item_id).eq("user_id", session["user_id"]).execute()
    flash("장바구니에서 뺐습니다.")
    return redirect(url_for("cart.view"))
