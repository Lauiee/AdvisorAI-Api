"""
교수님들의 이메일 주소를 임시로 업데이트하는 스크립트
"""
from database import SessionLocal, Professor

def update_professor_emails():
    """모든 교수님의 이메일 주소를 hm9720@naver.com으로 설정"""
    db = SessionLocal()
    try:
        # 모든 교수님 조회
        professors = db.query(Professor).all()
        
        if not professors:
            print("교수님 데이터가 없습니다.")
            return
        
        # 이메일 주소 업데이트
        temp_email = "hm9720@naver.com"
        updated_count = 0
        
        for professor in professors:
            professor.email = temp_email
            updated_count += 1
            print(f"✅ {professor.name} 교수님 ({professor.professor_id}) 이메일 업데이트: {temp_email}")
        
        db.commit()
        print(f"\n총 {updated_count}명의 교수님 이메일이 업데이트되었습니다.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_professor_emails()

