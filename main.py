"""
FastAPI 서버 - 학생-교수 트윈 MVP
- POST /match: 적합도 점수 계산
- POST /chat: RAG 기반 교수 트윈 응답
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from models import ProfessorTwinModel


def calculate_keyword_match_score(
    student_keywords: List[str], 
    professor_keywords: List[str]
) -> float:
    """
    키워드 매칭 점수 계산 (Jaccard 유사도) - 모델 없이도 사용 가능
    
    Args:
        student_keywords: 학생이 선택한 키워드 리스트
        professor_keywords: 교수 키워드 리스트
        
    Returns:
        0~1 사이의 키워드 매칭 점수
    """
    if not student_keywords or not professor_keywords:
        return 0.0
    
    student_set = set(student_keywords)
    professor_set = set(professor_keywords)
    
    intersection = len(student_set & professor_set)
    union = len(student_set | professor_set)
    
    if union == 0:
        return 0.0
    
    return intersection / union

# 샘플 데이터
SAMPLE_PROFESSOR_QA = [
    {"question": "연구 분야는 무엇인가요?", "answer": "인공지능과 머신러닝, 특히 자연어 처리 분야를 연구하고 있습니다."},
    {"question": "학부생도 연구에 참여할 수 있나요?", "answer": "네, 학부생도 연구에 참여할 수 있습니다. 관심 있는 학생은 이메일로 문의해주세요."},
    {"question": "추천하는 공부 방법은?", "answer": "기본 이론을 탄탄히 하고, 실제 프로젝트를 통해 경험을 쌓는 것을 추천합니다."},
    {"question": "석사 과정은 어떤가요?", "answer": "석사 과정에서는 심화된 연구와 논문 작성이 중요합니다. 약 2년 정도 소요됩니다."},
    {"question": "박사 과정 진학을 고려해야 할까요?", "answer": "연구에 대한 깊은 열정이 있고 학계나 연구소에서 일하고 싶다면 박사 과정을 추천합니다."},
    {"question": "인턴십은 어떻게 찾나요?", "answer": "대학원 사무실이나 온라인 채용 사이트를 통해 인턴십 기회를 찾을 수 있습니다."},
    {"question": "논문 작성 팁은?", "answer": "명확한 문제 정의와 체계적인 실험 설계가 중요합니다. 선행 연구를 충분히 조사하세요."},
    {"question": "코딩 실력이 부족한데 괜찮을까요?", "answer": "기본적인 프로그래밍 능력은 필요하지만, 연구 과정에서 계속 발전시킬 수 있습니다."},
    {"question": "연구실 분위기는 어떤가요?", "answer": "협력적이고 열린 분위기입니다. 정기적인 미팅과 토론을 통해 함께 성장합니다."},
    {"question": "졸업 후 진로는?", "answer": "대학원 졸업생들은 대기업 연구소, 스타트업, 대학 교수 등 다양한 진로를 선택합니다."},
    {"question": "수학 배경이 필요한가요?", "answer": "선형대수, 확률론, 미적분 등 기본적인 수학 지식이 도움이 됩니다."},
    {"question": "연구 주제는 어떻게 정하나요?", "answer": "최신 논문을 읽고, 관심 있는 분야를 탐색하며, 교수님과 상의하여 결정합니다."},
    {"question": "학점이 중요한가요?", "answer": "학점도 중요하지만, 연구 능력과 열정이 더 중요합니다."},
    {"question": "대학원 생활은 어떤가요?", "answer": "자율적이지만 책임감 있는 생활입니다. 연구에 몰입할 수 있는 환경입니다."},
    {"question": "장학금은 받을 수 있나요?", "answer": "연구 조교(RA)나 교육 조교(TA)를 통해 장학금을 받을 수 있습니다."},
    {"question": "해외 학회 참여는 가능한가요?", "answer": "네, 논문이 채택되면 해외 학회에 참여할 기회가 있습니다."},
    {"question": "워라밸은 지킬 수 있나요?", "answer": "연구는 집중이 필요하지만, 개인의 시간 관리로 균형을 맞출 수 있습니다."},
    {"question": "석사와 박사 차이는?", "answer": "석사는 2년, 박사는 4-5년 정도 소요되며, 박사는 더 깊은 연구가 필요합니다."},
    {"question": "취업 준비는 언제 시작하나요?", "answer": "졸업 1년 전부터 이력서 준비와 면접 연습을 시작하는 것을 추천합니다."},
    {"question": "연구실 선택 기준은?", "answer": "연구 분야, 교수님과의 궁합, 연구실 분위기 등을 종합적으로 고려하세요."},
]

SAMPLE_PROFESSOR_KEYWORDS = [
    "인공지능", "머신러닝", "자연어처리", "딥러닝", "연구", 
    "논문", "학회", "대학원", "석사", "박사"
]

# FastAPI 앱 초기화
app = FastAPI(
    title="학생-교수 트윈 MVP API",
    description="학생과 교수의 적합도를 계산하고 교수 트윈 AI와 채팅할 수 있는 API",
    version="1.0.0"
)

# 모델 인스턴스 (앱 시작 시 초기화)
model: Optional[ProfessorTwinModel] = None


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 교수 데이터 로드 및 임베딩 생성"""
    global model
    try:
        model = ProfessorTwinModel()
        model.load_professor_data(SAMPLE_PROFESSOR_QA, SAMPLE_PROFESSOR_KEYWORDS)
        print("✅ 교수 데이터 로드 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        print("⚠️  OPENAI_API_KEY 환경변수를 확인하세요.")


# Pydantic 모델 정의
class MatchRequest(BaseModel):
    """적합도 계산 요청 모델"""
    student_keywords: List[str]
    professor_keywords: Optional[List[str]] = None  # 선택사항 (기본값 사용 가능)


class MatchResponse(BaseModel):
    """적합도 계산 응답 모델"""
    fitness_score: float
    keyword_match_score: float
    qa_similarity_score: Optional[float] = None
    message: str


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    question: str


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    answer: str
    relevant_qa: List[dict]  # 참조된 QA 정보


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "학생-교수 트윈 MVP API",
        "endpoints": {
            "POST /match": "적합도 점수 계산",
            "POST /chat": "교수 트윈과 채팅"
        }
    }


@app.post("/match", response_model=MatchResponse)
async def calculate_match(request: MatchRequest):
    """
    학생-교수 적합도 점수 계산
    
    - 키워드 매칭 점수 계산 (모델 없이도 작동)
    - QA 임베딩 유사도 계산 (모델이 로드된 경우에만 가능)
    - 가중치 합산으로 최종 적합도 점수 반환
    """
    try:
        # 교수 키워드 결정 (요청에 없으면 기본값 사용)
        professor_keywords = request.professor_keywords or SAMPLE_PROFESSOR_KEYWORDS
        
        # 키워드 매칭 점수 (모델 없이도 계산 가능)
        keyword_score = calculate_keyword_match_score(
            request.student_keywords,
            professor_keywords
        )
        
        # 모델이 로드된 경우 QA 유사도도 계산 가능
        qa_similarity_score = None
        if model is not None:
            try:
                # 모델이 있으면 적합도 점수를 모델을 통해 계산
                fitness_score = model.calculate_fitness_score(
                    student_keywords=request.student_keywords,
                    keyword_weight=1.0,
                    qa_weight=0.0
                )
            except Exception:
                # 모델 오류 시 키워드 점수만 사용
                fitness_score = keyword_score
        else:
            # 모델이 없으면 키워드 점수만 사용
            fitness_score = keyword_score
        
        return MatchResponse(
            fitness_score=fitness_score,
            keyword_match_score=keyword_score,
            qa_similarity_score=qa_similarity_score,
            message=f"적합도 점수: {fitness_score:.3f} (키워드 매칭: {keyword_score:.3f})"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"적합도 계산 중 오류 발생: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat_with_professor_twin(request: ChatRequest):
    """
    교수 트윈과 채팅 (RAG 기반)
    
    - 학생 질문에 대해 관련된 상위 3개 QA 검색
    - LLM을 사용하여 교수 트윈 스타일의 답변 생성
    """
    if model is None:
        raise HTTPException(status_code=500, detail="모델이 초기화되지 않았습니다.")
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
    
    try:
        # 관련 QA 검색
        relevant_qa = model.search_relevant_qa(request.question, top_k=3)
        
        # RAG 응답 생성
        answer = model.generate_rag_response(request.question, top_k=3)
        
        # 참조된 QA 정보 포맷팅
        relevant_qa_info = [
            {
                "question": qa["question"],
                "answer": qa["answer"],
                "similarity_score": float(score)
            }
            for qa, score in relevant_qa
        ]
        
        return ChatResponse(
            answer=answer,
            relevant_qa=relevant_qa_info
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 응답 생성 중 오류 발생: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

