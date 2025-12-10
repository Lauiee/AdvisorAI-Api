"""
박진혁 교수님의 정보를 업데이트하는 스크립트
"""
from database import SessionLocal, Professor, GraduateSchool

def update_professor_jinhyeok():
    """박진혁 교수님의 정보를 업데이트"""
    db = SessionLocal()
    try:
        # 박진혁 교수님 조회
        professor = db.query(Professor).filter(Professor.professor_id == "prof_003").first()
        
        if not professor:
            print("❌ 박진혁 교수님(prof_003)을 찾을 수 없습니다.")
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
        new_major = "혁신전략 전공"
        new_research_fields = "기술혁신, 국제경영, 다국적 기업의 지식재산, R&D투자, M&A"
        new_introduction = "박진혁 교수는 현재 서강대학교 기술경영전문대학원의 혁신전략 전공의 부교수로 재직하고 있다. 네덜란드 마스트리히트 대학에서 UNU-MERIT 소속의 연구원으로 활동하며 경제학(혁신전략 전공) 박사학위를 취득하였으며, 서울대학교에서 경제학 석사와 학사 학위를 받았다. 서강대학교 부임 이전에는 프랑스의 네오마 경영대학 (NEOMA Business School)에서 4년간 조교수로 재직하였다. 기술혁신과 국제경영의 제반 분야를 연구하며 특히 다국적 기업의 지식재산, R&D투자, M&A에 대해서 연구하고 있다. 주요 연구성과들은 Strategic Management Journal, Industrial and Corporate Change 등 국제 탑저널에 게재되었으며 현재 한국기술경영경제학회, 한국전략경영학회 이사와 세계전략경영학회(SMS)의 운영위원(engagement officer)으로 활동하고 있다."
        new_education = "\n".join([
            "Ph.D. Economics and Innovation Strategy, Maastricht University",
            "M.A. 서울대학교 경제학부",
            "B.A. 서울대학교 경제학부"
        ])
        new_career = "\n".join([
            "2019.08 ~ 2023.08 프랑스 NEOMA 경영대학 조교수",
            "2015.09 ~ 2019.07 네덜란드 UNU-MERIT Ph.D Fellow"
        ])
        new_courses = "\n".join([
            "기술경영 연구방법론",
            "기술혁신론"
        ])
        
        # 정보 업데이트
        professor.major = new_major
        professor.research_fields = new_research_fields
        professor.introduction = new_introduction
        professor.education = new_education
        professor.career = new_career
        professor.courses = new_courses
        
        # 대학원 ID 확인 및 업데이트 (서강대학교 기술경영전문대학원)
        graduate_school = db.query(GraduateSchool).filter(
            GraduateSchool.name.like("%기술경영전문대학원%")
        ).first()
        
        if graduate_school:
            professor.graduate_school_id = graduate_school.id
            print(f"✅ 대학원 ID 업데이트: {graduate_school.name} (ID: {graduate_school.id})")
        
        db.commit()
        
        print("=== 업데이트 완료 ===")
        print(f"✅ 박진혁 교수님 ({professor.professor_id})의 정보가 업데이트되었습니다.")
        print()
        print("=== 업데이트된 정보 ===")
        print(f"전공: {professor.major}")
        print(f"연구 분야: {professor.research_fields}")
        print(f"소개: {professor.introduction[:100]}...")
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
    update_professor_jinhyeok()

