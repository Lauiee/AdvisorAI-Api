"""
박현규 교수님의 정보를 업데이트하는 스크립트
"""
from database import SessionLocal, Professor

def update_professor_park():
    """박현규 교수님의 정보를 업데이트"""
    db = SessionLocal()
    try:
        # 박현규 교수님 조회
        professor = db.query(Professor).filter(Professor.professor_id == "prof_001").first()
        
        if not professor:
            print("❌ 박현규 교수님(prof_001)을 찾을 수 없습니다.")
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
        new_major = "기술경영학"
        new_research_fields = "디지털 기업가 정신, 전략기획도구, 정성연구방법론"
        new_introduction = ""  # 빈 문자열
        new_education = "\n".join([
            "Ph.D. in Technology and Innovation Management, University of Cambridge",
            "M.A. MEng in Human Computer Interaction, Seoul National University",
            "B.A. BA in Anthropology (Ethnographic Studies), Chung-Ang University"
        ])
        new_career = "\n".join([
            "2021.03 ~ 현재 서강대학교 기술경영전문대학원 교수",
            "2020.09 ~ 2021.02 서섹스대학교 경영대학 교수",
            "2018.05 ~ 2020.08 캠브리지대학교 공과대학 연구교수",
            "2012.06 ~ 2014.06 LG CNS 선임연구원"
        ])
        new_courses = "\n".join([
            "기술혁신론",
            "기술로드매핑 이론과 실습",
            "정성연구와 사례개발"
        ])
        
        # 정보 업데이트
        professor.major = new_major
        professor.research_fields = new_research_fields
        professor.introduction = new_introduction
        professor.education = new_education
        professor.career = new_career
        professor.courses = new_courses
        
        db.commit()
        
        print("=== 업데이트 완료 ===")
        print(f"✅ 박현규 교수님 ({professor.professor_id})의 정보가 업데이트되었습니다.")
        print()
        print("=== 업데이트된 정보 ===")
        print(f"전공: {professor.major}")
        print(f"연구 분야: {professor.research_fields}")
        print(f"소개: {professor.introduction if professor.introduction else '(없음)'}")
        print(f"학력:\n{professor.education}")
        print(f"경력:\n{professor.career}")
        print(f"담당 과목:\n{professor.courses}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_professor_park()

