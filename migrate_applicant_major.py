"""
지원자 테이블에 major 컬럼 추가 마이그레이션
"""
import sqlite3
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 경로
DB_PATH = os.getenv("DATABASE_PATH", "./ai_adviser.db")

def migrate():
    """지원자 테이블에 major 컬럼 추가"""
    if not os.path.exists(DB_PATH):
        print(f"데이터베이스 파일 {DB_PATH}를 찾을 수 없습니다.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # major 컬럼이 이미 있는지 확인
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "major" not in columns:
            print("지원자 테이블에 major 컬럼을 추가합니다...")
            cursor.execute("ALTER TABLE applicants ADD COLUMN major VARCHAR(100)")
            conn.commit()
            print("✅ major 컬럼이 성공적으로 추가되었습니다.")
        else:
            print("✅ major 컬럼이 이미 존재합니다.")
        
        # professors 테이블에 email 컬럼이 있는지 확인
        cursor.execute("PRAGMA table_info(professors)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "email" not in columns:
            print("교수님 테이블에 email 컬럼을 추가합니다...")
            cursor.execute("ALTER TABLE professors ADD COLUMN email VARCHAR(200)")
            conn.commit()
            print("✅ email 컬럼이 성공적으로 추가되었습니다.")
        else:
            print("✅ email 컬럼이 이미 존재합니다.")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류가 발생했습니다: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

