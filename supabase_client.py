import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")                  # 공개 키 (로그인 확인용)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # 서버 전용 키 (절대 공개 금지)

# 데이터 읽기/쓰기는 서버 전용 키로 합니다.
# 브라우저에는 이 키가 절대 전달되지 않으므로 안전합니다.
db = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def new_auth_client():
    """로그인/회원가입 확인용 클라이언트를 매번 새로 만듭니다.
    (한 사람의 로그인 상태가 다른 사람과 섞이지 않게 하기 위해)"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)
