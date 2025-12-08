"""
데이터베이스 초기화 및 기본 데이터 입력 스크립트
사용자가 직접 기본 정보를 입력할 수 있도록 구성
"""
from database import init_db, SessionLocal, GraduateSchool, Professor

def create_sample_data():
    """샘플 데이터 생성 (실제 데이터는 사용자가 직접 입력)"""
    db = SessionLocal()
    
    try:
        # 대학원 생성 예시
        # 실제로는 사용자가 직접 입력
        graduate_school = GraduateSchool(
            name="서강대학교 기술경영전문대학원",
            description="기술경영 분야의 전문 대학원"
        )
        db.add(graduate_school)
        db.commit()
        db.refresh(graduate_school)
        
        # 교수님 생성 예시
        # 실제로는 사용자가 직접 입력
        professor = Professor(
            professor_id="prof_001",
            name="박현규",
            graduate_school_id=graduate_school.id,
            major="기술경영학",
            research_fields="디지털 기업가 정신, 전략기획도구, 정성연구방법론",
            introduction="박현규 교수는 University of Cambridge에서 기술경영학 박사학위를 취득하고 현재 서강대학교 기술경영전문대학원 부교수로 재직 중이다.",
            education="Ph.D. Technology and Innovation Management, University of Cambridge",
            career="2021.03~현재 서강대학교 기술경영전문대학원 교수",
            courses="기술혁신론, 기술로드매핑 이론과 실습, 정성연구와 사례개발"
        )
        db.add(professor)
        db.commit()
        
        print("샘플 데이터가 생성되었습니다.")
        
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("데이터베이스 초기화 중...")
    init_db()
    print("데이터베이스 테이블이 생성되었습니다.")
    
    # 샘플 데이터 생성 여부 확인
    response = input("샘플 데이터를 생성하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        create_sample_data()

