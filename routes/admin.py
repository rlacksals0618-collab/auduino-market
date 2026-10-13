import time

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from routes.helpers import admin_required, error_message, to_int
from supabase_client import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ORDER_STATUSES = ["주문완료", "배송준비", "배송중", "배송완료", "주문취소"]
BUCKET = "product-images"


def upload_image(file):
    """관리자가 올린 이미지를 Supabase Storage에 저장하고 공개 주소를 돌려줍니다."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
        raise ValueError("jpg, png, webp, gif 이미지만 올릴 수 있습니다.")
    path = f"products/{int(time.time() * 1000)}.{ext}"
    db.storage.from_(BUCKET).upload(path, file.read(), {"content-type": file.mimetype})
    return db.storage.from_(BUCKET).get_public_url(path).rstrip("?")


def read_product_form():
    specs = [line.strip() for line in request.form.get("specs", "").splitlines() if line.strip()]
    return {
        "name": request.form.get("name", "").strip(),
        "category_id": to_int(request.form.get("category_id")) or None,
        "price": max(0, to_int(request.form.get("price"))),
        "stock": max(0, to_int(request.form.get("stock"))),
        "description": request.form.get("description", "").strip(),
        "specs": specs,
        "devicemart_url": request.form.get("devicemart_url", "").strip() or None,
    }


@admin_bp.route("/")
@admin_required
def products():
    rows = db.table("products").select("*, categories(name)").order("id").execute().data
    return render_template("admin/products.html", products=rows)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    return product_form(None)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    found = db.table("products").select("*").eq("id", product_id).execute().data
    if not found:
        abort(404)
    return product_form(found[0])


def product_form(product):
    categories = db.table("categories").select("*").order("sort_order").execute().data

    if request.method == "POST":
        data = read_product_form()
        if not data["name"]:
            flash("상품명을 입력하세요.", "error")
            return render_template("admin/product_form.html", product=data, categories=categories)
        try:
            image = request.files.get("image")
            if image and image.filename:
                data["image_url"] = upload_image(image)
                # 직접 올린 이미지이므로 무료 이미지 출처 정보는 지움
                data.update(image_source=None, image_license=None, image_author=None)

            if product:
                db.table("products").update(data).eq("id", product["id"]).execute()
                flash("상품을 수정했습니다.")
            else:
                data["slug"] = f"p-{int(time.time())}"
                db.table("products").insert(data).execute()
                flash("상품을 등록했습니다.")
            return redirect(url_for("admin.products"))
        except Exception as e:
            flash(f"저장 실패: {error_message(e)}", "error")
            product = {**(product or {}), **data}

    return render_template("admin/product_form.html", product=product, categories=categories)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id):
    db.table("products").delete().eq("id", product_id).execute()
    flash("상품을 삭제했습니다.")
    return redirect(url_for("admin.products"))


@admin_bp.route("/orders")
@admin_required
def orders():
    rows = db.table("orders").select("*, order_items(*)").order("id", desc=True).execute().data
    emails = {p["id"]: p["email"] for p in db.table("profiles").select("id, email").execute().data}
    return render_template("admin/orders.html", orders=rows, emails=emails, statuses=ORDER_STATUSES)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    status = request.form.get("status")
    if status in ORDER_STATUSES:
        db.table("orders").update({"status": status}).eq("id", order_id).execute()
        flash(f"주문 {order_id}번 상태를 '{status}'(으)로 바꿨습니다.")
    return redirect(url_for("admin.orders"))
