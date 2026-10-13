import os

from dotenv import load_dotenv
from flask import Flask, session, url_for

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.products import products_bp
from supabase_client import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 업로드 이미지 최대 5MB

app.register_blueprint(products_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(admin_bp)


@app.template_filter("won")
def won(value):
    """12000 -> 12,000원"""
    return f"{int(value or 0):,}원"


@app.template_filter("datetime")
def datetime_text(value):
    """2026-10-13T06:39:26+00:00 -> 2026-10-13 06:39"""
    return (value or "")[:16].replace("T", " ")


@app.template_global()
def image_src(url):
    """DB에 저장된 이미지 경로를 화면에서 쓸 주소로 바꿉니다."""
    if not url:
        return ""
    if url.startswith("http"):
        return url
    return url_for("static", filename=url)


@app.context_processor
def inject_common():
    """모든 화면에서 쓰는 값: 카테고리 메뉴, 장바구니 개수"""
    categories = db.table("categories").select("*").order("sort_order").execute().data
    cart_count = 0
    if "user_id" in session:
        items = db.table("cart_items").select("quantity").eq("user_id", session["user_id"]).execute().data
        cart_count = sum(i["quantity"] for i in items)
    return {"nav_categories": categories, "cart_count": cart_count}


if __name__ == "__main__":
    app.run(debug=True)
