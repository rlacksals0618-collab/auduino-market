"""products.json의 상품을 Supabase에 넣습니다. (여러 번 실행해도 중복되지 않음)

실행: 1013 폴더에서  python database/seed.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import db  # noqa: E402

CATEGORIES = [
    {"slug": "boards", "name": "보드", "sort_order": 1},
    {"slug": "sensors", "name": "센서", "sort_order": 2},
    {"slug": "motors", "name": "모터·구동", "sort_order": 3},
    {"slug": "kits", "name": "부품·키트", "sort_order": 4},
]

db.table("categories").upsert(CATEGORIES, on_conflict="slug").execute()
category_ids = {c["name"]: c["id"] for c in db.table("categories").select("id, name").execute().data}

json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")
with open(json_path, encoding="utf-8") as f:
    products = json.load(f)

rows = []
for p in products:
    rows.append({
        "slug": p["slug"],
        "name": p["name"],
        "category_id": category_ids[p["category"]],
        "price": p["price"],
        "stock": p["stock"],
        "description": p["description"],
        "specs": p["specs"],
        "image_url": p["image"],
        "devicemart_url": p["devicemart_url"],
        "image_source": p["image_source"],
        "image_license": p["image_license"],
        "image_author": p["image_author"],
    })

db.table("products").upsert(rows, on_conflict="slug").execute()
print(f"카테고리 {len(CATEGORIES)}개, 상품 {len(rows)}개를 넣었습니다.")
