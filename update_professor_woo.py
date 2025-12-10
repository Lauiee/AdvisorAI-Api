"""
우한균 교수님의 정보를 업데이트하는 스크립트
"""
from database import SessionLocal, Professor

def update_professor_woo():
    """우한균 교수님의 정보를 업데이트"""
    db = SessionLocal()
    try:
        # 우한균 교수님 조회
        professor = db.query(Professor).filter(Professor.professor_id == "prof_002").first()
        
        if not professor:
            print("❌ 우한균 교수님(prof_002)을 찾을 수 없습니다.")
            return
        
        # 현재 정보 출력
        print("=== 현재 정보 ===")
        print(f"이름: {professor.name}")
        print(f"전공: {professor.major}")
        print(f"연구 분야: {professor.research_fields}")
        print(f"소개: {professor.introduction}")
        print(f"학력: {professor.education}")
        print(f"경력: {professor.career}")
        print(f"담당 과목: {professor.courses}")
        print()
        
        # 업데이트할 정보
        new_education = "\n".join([
            "Ph.D. Computer Information Systems, Georgia State University",
            "M.A. 서울대학교 경영학과",
            "B.A. 서울대학교 경영학과"
        ])
        
        new_career = "\n".join([
            "2022.09 ~ 현재 서강대학교 기술경영전문대학원 교수",
            "2017.03 ~ 2022.08 울산과학기술원(UNIST) 기술경영전문대학원, 부교수",
            "2009.12 ~ 2017.02 울산과학기술원(UNIST) 경영학부, 조교수",
            "2009.02 ~ 2009.12 테크노베이션 파트너스, 수석컨설턴트",
            "2004.09 ~ 2009.01 Le Moyne College 경영학부, 조교수"
        ])
        
        new_courses = "\n".join([
            "석사 : 기술경영개론, 기술경영 연구방법론, 의사결정 지원을 위한 인공지능의 활용",
            "학사 : AI 기반 기술경영 및 정책"
        ])
        
        # 정보 업데이트
        professor.education = new_education
        professor.career = new_career
        professor.courses = new_courses
        
        db.commit()
        
        print("=== 업데이트 완료 ===")
        print(f"✅ 우한균 교수님 ({professor.professor_id})의 정보가 업데이트되었습니다.")
        print()
        print("=== 업데이트된 정보 ===")
        print(f"학력:\n{professor.education}")
        print()
        print(f"경력:\n{professor.career}")
        print()
        print(f"담당 과목:\n{professor.courses}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_professor_woo()

