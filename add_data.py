"""
교수님 기본 정보를 데이터베이스에 추가하는 스크립트
사용자가 직접 데이터를 입력할 수 있습니다.
"""
from database import SessionLocal, GraduateSchool, Professor

def add_graduate_school(name: str, education_fields: str = None, keywords: str = None):
    """대학원 추가"""
    db = SessionLocal()
    try:
        school = GraduateSchool(
            name=name,
            education_fields=education_fields,
            keywords=keywords
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        print(f"대학원이 추가되었습니다: {school.name} (ID: {school.id})")
        return school
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        return None
    finally:
        db.close()


def add_professor(
    professor_id: str,
    name: str,
    graduate_school_id: int,
    major: str = None,
    research_fields: str = None,
    introduction: str = None,
    education: str = None,
    career: str = None,
    courses: str = None
):
    """교수님 추가"""
    db = SessionLocal()
    try:
        professor = Professor(
            professor_id=professor_id,
            name=name,
            graduate_school_id=graduate_school_id,
            major=major,
            research_fields=research_fields,
            introduction=introduction,
            education=education,
            career=career,
            courses=courses
        )
        db.add(professor)
        db.commit()
        db.refresh(professor)
        print(f"교수님이 추가되었습니다: {professor.name} (ID: {professor.id})")
        return professor
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        return None
    finally:
        db.close()


def list_graduate_schools():
    """대학원 목록 조회"""
    db = SessionLocal()
    try:
        schools = db.query(GraduateSchool).all()
        print("\n=== 대학원 목록 ===")
        for school in schools:
            print(f"ID: {school.id}, 이름: {school.name}")
        return schools
    finally:
        db.close()


if __name__ == "__main__":
    print("=== 데이터 추가 도구 ===\n")
    
    while True:
        print("\n1. 대학원 추가")
        print("2. 교수님 추가")
        print("3. 대학원 목록 조회")
        print("4. 종료")
        
        choice = input("\n선택: ")
        
        if choice == "1":
            name = input("대학원 명: ")
            education_fields = input("대학원 교육 분야 (예: 기술경영, 기술혁신) (선택사항): ")
            keywords = input("키워드 (예: 기술 전략, AI전환, 창업) (선택사항): ")
            add_graduate_school(
                name,
                education_fields if education_fields else None,
                keywords if keywords else None
            )
            
        elif choice == "2":
            list_graduate_schools()
            school_id = int(input("\n대학원 ID: "))
            professor_id = input("교수님 ID (예: prof_001): ")
            name = input("교수님 이름: ")
            major = input("전공 (선택사항): ")
            research_fields = input("연구 분야 (선택사항): ")
            introduction = input("소개 (선택사항): ")
            education = input("학력 (선택사항): ")
            career = input("경력 (선택사항): ")
            courses = input("담당 과목 (선택사항): ")
            
            add_professor(
                professor_id=professor_id,
                name=name,
                graduate_school_id=school_id,
                major=major if major else None,
                research_fields=research_fields if research_fields else None,
                introduction=introduction if introduction else None,
                education=education if education else None,
                career=career if career else None,
                courses=courses if courses else None
            )
            
        elif choice == "3":
            list_graduate_schools()
            
        elif choice == "4":
            print("종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

