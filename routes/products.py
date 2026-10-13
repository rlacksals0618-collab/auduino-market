from flask import Blueprint, abort, render_template, request

from supabase_client import db

products_bp = Blueprint("products", __name__)

PRODUCT_FIELDS = "*, categories(name, slug)"


@products_bp.route("/")
def index():
    category_slug = request.args.get("category", "")
    keyword = request.args.get("q", "").strip()

    query = db.table("products").select(PRODUCT_FIELDS)

    current_category = None
    if category_slug:
        found = db.table("categories").select("*").eq("slug", category_slug).execute().data
        if found:
            current_category = found[0]
            query = query.eq("category_id", current_category["id"])

    if keyword:
        query = query.ilike("name", f"%{keyword}%")

    products = query.order("category_id").order("id").execute().data
    return render_template(
        "index.html",
        products=products,
        current_category=current_category,
        keyword=keyword,
    )


@products_bp.route("/products/<int:product_id>")
def detail(product_id):
    found = db.table("products").select(PRODUCT_FIELDS).eq("id", product_id).execute().data
    if not found:
        abort(404)
    return render_template("product_detail.html", product=found[0])


@products_bp.route("/credits")
def credits():
    products = (
        db.table("products")
        .select("name, image_source, image_license, image_author")
        .not_.is_("image_source", "null")
        .order("id")
        .execute()
        .data
    )
    return render_template("credits.html", products=products)
