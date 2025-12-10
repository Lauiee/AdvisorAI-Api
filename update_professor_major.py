"""
박현규 교수님의 전공을 수정하는 스크립트
"""
from database import SessionLocal, Professor

def update_professor_major():
    """박현규 교수님의 전공을 '기술경영학'으로 수정"""
    db = SessionLocal()
    try:
        # 박현규 교수님 조회
        professor = db.query(Professor).filter(Professor.name == "박현규").first()
        
        if not professor:
            print("❌ 박현규 교수님을 찾을 수 없습니다.")
            return
        
        # 현재 전공 확인
        current_major = professor.major
        print(f"현재 전공: {current_major}")
        
        # 전공 수정 (띄어쓰기 제거)
        professor.major = "기술경영학"
        
        db.commit()
        print(f"✅ 박현규 교수님 ({professor.professor_id})의 전공이 '{professor.major}'로 업데이트되었습니다.")
        print(f"   변경 전: {current_major}")
        print(f"   변경 후: {professor.major}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_professor_major()

