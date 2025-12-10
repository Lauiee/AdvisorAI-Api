"""
박현규 교수님의 introduction을 업데이트하는 스크립트
"""
from database import SessionLocal, Professor

def update_professor_introduction():
    """박현규 교수님의 introduction을 업데이트"""
    db = SessionLocal()
    try:
        # 박현규 교수님 조회
        professor = db.query(Professor).filter(Professor.professor_id == "prof_001").first()
        
        if not professor:
            print("❌ 박현규 교수님(prof_001)을 찾을 수 없습니다.")
            return
        
        # 업데이트할 introduction
        new_introduction = """박현규 교수는 영국 케임브리지대학교(University of Cambridge)에서 기술경영학 박사학위 취득 후 현재 서강대학교 기술경영전문대학원 부교수로 재직 중이다. 서강대학교 부임 전에는 영국 서섹스 대학교(University of Sussex) 경영대학 기술경영학과 조교수로 재직했다.

주요 연구분야는 기업가정신(Entrepreneurship)과 벤처투자(Venture investment)이며, 연구성과는 Strategic Entrepreneurship Journal(FT 50), British Journal of Management(ABS 4) 등 국제 저명 학술지에 게재되었다. 박현규 교수의 학술 연구는, 개인투자조합 GP, TIPS 등 정부지원사업 심사위원, LG CNS 개발자 경험을 통해 얻은 실무적 지식을 바탕으로 한다.

박현규 교수가 운영 중인 연구실(Centre for Open Entrepreneurship)은 기업용 인공지능(AI) 모델 및 제품을 개발하고, 데이터 마이닝(Data mining) 기반의 기술동향 분석을 수행한다. 대기업, 중소기업, 스타트업으로부터 꾸준히 협업 의뢰를 받고 있으며, 최근 3년간 총 12건 이상의 기업프로젝트를 성공적으로 완수했다."""
        
        # 현재 introduction 확인
        current_intro = professor.introduction
        print("=== 현재 introduction ===")
        print(current_intro if current_intro else "(없음)")
        print()
        
        # introduction 업데이트
        professor.introduction = new_introduction
        
        db.commit()
        
        print("=== 업데이트 완료 ===")
        print(f"✅ 박현규 교수님 ({professor.professor_id})의 introduction이 업데이트되었습니다.")
        print()
        print("=== 업데이트된 introduction ===")
        print(professor.introduction)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_professor_introduction()

