"""
데이터베이스 구조 마이그레이션 스크립트
description 필드를 education_fields와 keywords로 변경
"""
from sqlalchemy import text
from database import engine, SessionLocal, GraduateSchool

def migrate_database():
    """데이터베이스 구조 마이그레이션"""
    db = SessionLocal()
    
    try:
        # SQLite는 ALTER TABLE 제약이 있어서 단계별로 처리
        # 1. 새 컬럼 추가
        print("새 컬럼 추가 중...")
        db.execute(text("ALTER TABLE graduate_schools ADD COLUMN education_fields TEXT"))
        db.execute(text("ALTER TABLE graduate_schools ADD COLUMN keywords TEXT"))
        db.commit()
        print("새 컬럼이 추가되었습니다.")
        
        # 2. 기존 description 데이터 확인 (필요시 수동으로 education_fields/keywords로 이전)
        schools = db.query(GraduateSchool).all()
        if schools:
            print(f"\n기존 대학원 데이터 {len(schools)}개 발견:")
            for school in schools:
                print(f"  - ID: {school.id}, 이름: {school.name}")
                if hasattr(school, 'description') and school.description:
                    print(f"    기존 설명: {school.description}")
                    print("    → education_fields와 keywords를 수동으로 업데이트해주세요.")
        
        # 3. description 컬럼 제거 (SQLite는 직접 제거 불가, 무시해도 됨)
        print("\n마이그레이션 완료!")
        print("참고: SQLite는 컬럼 삭제를 지원하지 않으므로 description 컬럼은 남아있지만 사용하지 않습니다.")
        
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("컬럼이 이미 존재합니다. 마이그레이션이 이미 완료된 것 같습니다.")
        else:
            print(f"마이그레이션 중 오류 발생: {e}")
            db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=== 데이터베이스 마이그레이션 ===\n")
    migrate_database()

