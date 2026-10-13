import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key or "your-" in url or "your-" in key:
    raise SystemExit(".env 파일에 SUPABASE_URL과 SUPABASE_KEY를 먼저 입력하세요.")

supabase = create_client(url, key)
print("Supabase 클라이언트 생성 완료:", url)

# 연결 테스트: 테이블 이름을 본인 프로젝트의 테이블로 바꿔서 실행해 보세요
TABLE = "install"
try:
    response = supabase.table(TABLE).select("*").limit(5).execute()
    print(f"'{TABLE}' 테이블 조회 성공:", response.data)
except Exception as e:
    print(f"'{TABLE}' 테이블 조회 실패 (테이블이 없거나 권한(RLS) 문제일 수 있음):", e)
