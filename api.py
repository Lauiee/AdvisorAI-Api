from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import uvicorn
import json

# chat.py에서 함수들 import
from chat import generate_answer
# database 모델 및 의존성 import
from database import get_db, GraduateSchool, Professor, Applicant, ChatSession, ChatMessage
from database import init_db
# matching.py에서 매칭 함수 import
from matching import (
    calculate_matching_score, 
    match_all_professors, 
    generate_matching_rationale,
    calculate_chat_based_score,
    calculate_final_matching_score,
    generate_final_report,
    generate_email_draft
)
# email_sender.py에서 이메일 전송 함수 import
from email_sender import send_email
from datetime import datetime

# -----------------------------
# FastAPI 앱 생성
# -----------------------------
app = FastAPI(
    title="Advisor AI API",
    version="1.0.0",
    contact={
        "name": "Advisor AI API",
    },
)

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 요청/응답 모델
# -----------------------------
class ChatRequest(BaseModel):
    question: str = Field(..., description="사용자의 질문", example="교수님은 어떤 연구 방법론을 선호하시나요?")
    professor_id: Optional[str] = Field(None, description="교수님 ID (예: prof_001). 지정하면 해당 교수님의 데이터만 검색합니다.", example="prof_001")
    top_k: Optional[int] = Field(3, description="검색할 관련 정보 개수", ge=1, le=10, example=3)
    session_id: Optional[int] = Field(None, description="채팅 세션 ID. 지정하면 메시지가 데이터베이스에 저장됩니다.", example=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "교수님은 어떤 연구 방법론을 선호하시나요?",
                "professor_id": "prof_001",
                "top_k": 3,
                "session_id": 1
            }
        }


class Reference(BaseModel):
    title: str
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="교수님 트윈 AI의 답변", example="저는 개인적으로 정성적 분석과 사례 연구를 선호합니다...")
    references: List[str] = Field(..., description="답변 생성에 참고한 정보 목록", example=["- 연구 방법론은 어떤 방식을 선호하시나요?", "- 연구 주제는 어떻게 정하나요?"])
    success: bool = Field(True, description="요청 성공 여부")
    session_id: Optional[int] = Field(None, description="채팅 세션 ID", example=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "저는 개인적으로 정성적 분석과 사례 연구를 선호합니다. 실제 기업 사례를 통해 이론을 검증하는 방식을 좋아합니다.",
                "references": [
                    "- 연구 방법론은 어떤 방식을 선호하시나요?",
                    "- 연구 주제는 어떻게 정하나요?"
                ],
                "success": True,
                "session_id": 1
            }
        }


# -----------------------------
# 채팅 세션 관련 요청/응답 모델
# -----------------------------
class ChatSessionRequest(BaseModel):
    applicant_id: int = Field(..., description="지원자 ID", example=1)
    professor_id: str = Field(..., description="교수님 ID (예: prof_001)", example="prof_001")
    
    class Config:
        json_schema_extra = {
            "example": {
                "applicant_id": 1,
                "professor_id": "prof_001"
            }
        }


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    applicant_id: int
    professor_id: str
    professor_name: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int
    messages: List[ChatMessageResponse] = []
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    message: str


# -----------------------------
# 대학원/교수님 관련 응답 모델
# -----------------------------
class GraduateSchoolResponse(BaseModel):
    id: int
    name: str
    education_fields: Optional[str] = None  # 대학원 교육 분야
    keywords: Optional[str] = None  # 키워드
    
    class Config:
        from_attributes = True


class ProfessorBasicInfo(BaseModel):
    id: int
    professor_id: str
    name: str
    major: Optional[str] = None
    research_fields: Optional[str] = None
    introduction: Optional[str] = None
    education: Optional[str] = None
    career: Optional[str] = None
    courses: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProfessorsListResponse(BaseModel):
    graduate_school: GraduateSchoolResponse
    professors: List[ProfessorBasicInfo]
    total_count: int


# -----------------------------
# 매칭 관련 요청/응답 모델
# -----------------------------
class ApplicantRequest(BaseModel):
    name: Optional[str] = Field(None, description="지원자 이름 (선택사항)", example="홍길동")
    major: Optional[str] = Field(None, description="전공 (선택사항)", example="경영학과")
    interest_keyword: str = Field(..., description="관심 키워드 (필수)", example="디지털 전환")
    learning_styles: List[str] = Field(..., description="학습 성향 (필수, 여러 개 선택 가능)", example=["사례 기반", "협업형"])
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "홍길동",
                "major": "경영학과",
                "interest_keyword": "디지털 전환",
                "learning_styles": ["사례 기반", "협업형", "탐구형"]
            }
        }


class IndicatorScore(BaseModel):
    indicator: str  # Indicator 카테고리 (A, B, C, D, E)
    score: float  # Indicator별 적합도 점수 (100점 만점)
    qa_count: int  # 해당 indicator의 Q&A 개수
    details: List[dict]  # 상세 매칭 정보


class MatchingResult(BaseModel):
    professor_id: str
    professor_name: Optional[str] = None
    total_score: float  # 최종 적합도 (0-100%, 5개 indicator의 평균)
    indicator_scores: List[IndicatorScore]  # 각 indicator별 점수 (100점 만점)
    breakdown: dict  # 각 indicator별 점수 요약
    rationale: Optional[str] = None  # 매칭 근거 설명


class MatchingResponse(BaseModel):
    applicant_id: int  # 지원자 ID (항상 반환)
    results: List[MatchingResult]
    success: bool = True


# -----------------------------
# 지원자 정보 관련 요청/응답 모델
# -----------------------------
class ApplicantResponse(BaseModel):
    id: int
    name: Optional[str] = None
    major: Optional[str] = None
    interest_keyword: str
    learning_styles: str
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# -----------------------------
# 최종 리포트 관련 요청/응답 모델
# -----------------------------
class FinalReportResponse(BaseModel):
    session_id: int
    applicant_id: int
    professor_id: str
    professor_name: Optional[str] = None
    initial_score: int  # 1차 적합도
    chat_score: int  # 채팅 기반 점수
    final_score: int  # 최종 적합도
    report: str  # 리포트 내용 (채팅 분석 포함)
    success: bool = True


# -----------------------------
# 이메일 초안 관련 요청/응답 모델
# -----------------------------
class EmailDraftRequest(BaseModel):
    applicant_id: int
    professor_id: str
    session_id: Optional[int] = None  # 선택사항, 최종 리포트 정보 포함 시
    appointment_date: str  # 예: "2025년 12월 17일"
    appointment_time: str  # 예: "오후 3시 12분"
    consultation_method: str = "대면"  # "대면", "zoom", "전화"


class EmailDraftResponse(BaseModel):
    email_draft: str  # 이메일 초안 내용
    success: bool = True


class EmailSendRequest(BaseModel):
    applicant_id: int
    professor_id: str
    email_subject: str  # 이메일 제목
    email_body: str  # 이메일 본문 (초안)
    from_email: Optional[str] = None  # 발신자 이메일 (선택사항)
    from_name: Optional[str] = None  # 발신자 이름 (선택사항)


class EmailSendResponse(BaseModel):
    success: bool
    message: str


# -----------------------------
# 데이터베이스 초기화 (앱 시작 시)
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 초기화"""
    init_db()


# -----------------------------
# API 엔드포인트
# -----------------------------
@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="API 상태 확인",
    description="API 서버의 기본 상태를 확인합니다."
)
async def root():
    """API 상태 확인"""
    return {
        "status": "healthy",
        "message": "AI Adviser API is running"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="헬스 체크",
    description="API 서버의 헬스 상태를 확인합니다."
)
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "API is operational"
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="교수님 트윈 AI와 채팅",
    description="""
    교수님 트윈 AI와 실시간으로 대화할 수 있는 엔드포인트입니다.
    
    RAG(Retrieval-Augmented Generation) 기반으로 교수님의 실제 답변과 정보를 검색하여
    교수님의 스타일로 답변을 생성합니다.
    
    **주요 기능:**
    - 교수님의 실제 Q&A 데이터를 기반으로 답변 생성
    - 교수님의 말투와 스타일로 자연스러운 답변
    - 관련 정보 자동 검색 및 참조 제공
    - 채팅 세션 지원 (메시지 저장 가능)
    """
)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    사용자 질문에 대한 답변 생성
    
    - **question**: 사용자의 질문
    - **professor_id**: 교수님 ID (필수, 예: "prof_001")
    - **top_k**: 검색할 관련 정보 개수 (기본값: 3)
    - **session_id**: 채팅 세션 ID (선택사항, 있으면 메시지 저장)
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="질문을 입력해주세요."
            )
        
        if not request.professor_id:
            raise HTTPException(
                status_code=400,
                detail="교수님 ID를 입력해주세요."
            )
        
        # RAG 기반 답변 생성 (professor_id로 필터링)
        answer, references = generate_answer(
            user_question=request.question,
            professor_id=request.professor_id,
            top_k=request.top_k
        )
        
        session_id = None
        # 세션이 있으면 메시지 저장
        if request.session_id:
            try:
                session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
                if session:
                    # 사용자 메시지 저장
                    user_message = ChatMessage(
                        session_id=session.id,
                        role="user",
                        content=request.question
                    )
                    db.add(user_message)
                    
                    # 교수님 답변 저장
                    professor_message = ChatMessage(
                        session_id=session.id,
                        role="professor",
                        content=answer
                    )
                    db.add(professor_message)
                    
                    # 세션 업데이트 시간 갱신
                    session.updated_at = datetime.utcnow()
                    
                    db.commit()
                    session_id = session.id
            except Exception as e:
                db.rollback()
                # 메시지 저장 실패해도 답변은 반환
        
        return ChatResponse(
            answer=answer,
            references=references,
            success=True,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"답변 생성 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 대학원/교수님 관련 API
# -----------------------------
@app.get(
    "/graduate-schools",
    response_model=List[GraduateSchoolResponse],
    tags=["Graduate Schools & Professors"],
    summary="대학원 목록 조회",
    description="등록된 모든 대학원의 목록을 조회합니다."
)
async def get_graduate_schools(db: Session = Depends(get_db)):
    """모든 대학원 목록 조회"""
    try:
        schools = db.query(GraduateSchool).all()
        return schools
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대학원 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get(
    "/graduate-schools/{school_id}/professors",
    response_model=ProfessorsListResponse,
    tags=["Graduate Schools & Professors"],
    summary="대학원별 교수님 목록 조회",
    description="특정 대학원에 소속된 교수님들의 목록과 기본 정보를 조회합니다."
)
async def get_professors_by_school(school_id: int, db: Session = Depends(get_db)):
    """
    특정 대학원의 교수님 목록과 기본 정보 조회
    
    - **school_id**: 대학원 ID
    """
    try:
        # 대학원 조회
        graduate_school = db.query(GraduateSchool).filter(GraduateSchool.id == school_id).first()
        if not graduate_school:
            raise HTTPException(
                status_code=404,
                detail=f"ID {school_id}에 해당하는 대학원을 찾을 수 없습니다."
            )
        
        # 해당 대학원의 교수님 목록 조회
        professors = db.query(Professor).filter(
            Professor.graduate_school_id == school_id
        ).all()
        
        return ProfessorsListResponse(
            graduate_school=graduate_school,
            professors=professors,
            total_count=len(professors)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"교수님 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 채팅 세션 관련 API
# -----------------------------
@app.post(
    "/chat/session",
    response_model=ChatSessionResponse,
    tags=["Chat"],
    summary="채팅 세션 생성",
    description="지원자와 교수님 간의 새로운 채팅 세션을 생성하거나 기존 세션을 조회합니다."
)
async def create_chat_session(
    request: ChatSessionRequest,
    db: Session = Depends(get_db)
):
    """
    채팅 세션 생성
    
    - **applicant_id**: 지원자 ID
    - **professor_id**: 교수님 ID (prof_001 등)
    """
    try:
        # 지원자 확인
        applicant = db.query(Applicant).filter(Applicant.id == request.applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {request.applicant_id}를 찾을 수 없습니다."
            )
        
        # 교수님 확인
        professor = db.query(Professor).filter(Professor.professor_id == request.professor_id).first()
        if not professor:
            raise HTTPException(
                status_code=404,
                detail=f"교수님 ID {request.professor_id}를 찾을 수 없습니다."
            )
        
        # 기존 세션이 있는지 확인 (같은 지원자-교수님 조합)
        existing_session = db.query(ChatSession).filter(
            ChatSession.applicant_id == request.applicant_id,
            ChatSession.professor_id == request.professor_id
        ).first()
        
        if existing_session:
            # 기존 세션 반환
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == existing_session.id
            ).count()
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == existing_session.id
            ).order_by(ChatMessage.timestamp).all()
            
            return ChatSessionResponse(
                id=existing_session.id,
                applicant_id=existing_session.applicant_id,
                professor_id=existing_session.professor_id,
                professor_name=professor.name,
                created_at=existing_session.created_at.isoformat(),
                updated_at=existing_session.updated_at.isoformat(),
                message_count=message_count,
                messages=[
                    ChatMessageResponse(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp.isoformat()
                    )
                    for msg in messages
                ]
            )
        
        # 새 세션 생성
        new_session = ChatSession(
            applicant_id=request.applicant_id,
            professor_id=request.professor_id
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return ChatSessionResponse(
            id=new_session.id,
            applicant_id=new_session.applicant_id,
            professor_id=new_session.professor_id,
            professor_name=professor.name,
            created_at=new_session.created_at.isoformat(),
            updated_at=new_session.updated_at.isoformat(),
            message_count=0,
            messages=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"채팅 세션 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.get(
    "/chat/session/{session_id}",
    response_model=ChatSessionResponse,
    tags=["Chat"],
    summary="채팅 세션 조회",
    description="특정 채팅 세션의 정보와 메시지 내역을 조회합니다."
)
async def get_chat_session(session_id: int, db: Session = Depends(get_db)):
    """채팅 세션 조회"""
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"세션 ID {session_id}를 찾을 수 없습니다."
            )
        
        professor = db.query(Professor).filter(
            Professor.professor_id == session.professor_id
        ).first()
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).all()
        
        return ChatSessionResponse(
            id=session.id,
            applicant_id=session.applicant_id,
            professor_id=session.professor_id,
            professor_name=professor.name if professor else None,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=len(messages),
            messages=[
                ChatMessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat()
                )
                for msg in messages
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"채팅 세션 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get(
    "/chat/sessions/applicant/{applicant_id}",
    response_model=List[ChatSessionResponse],
    tags=["Chat"],
    summary="지원자 채팅 세션 목록 조회",
    description="특정 지원자의 모든 채팅 세션 목록을 조회합니다."
)
async def get_applicant_sessions(applicant_id: int, db: Session = Depends(get_db)):
    """지원자의 모든 채팅 세션 조회"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.applicant_id == applicant_id
        ).order_by(ChatSession.updated_at.desc()).all()
        
        result = []
        for session in sessions:
            professor = db.query(Professor).filter(
                Professor.professor_id == session.professor_id
            ).first()
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.timestamp).all()
            
            result.append(ChatSessionResponse(
                id=session.id,
                applicant_id=session.applicant_id,
                professor_id=session.professor_id,
                professor_name=professor.name if professor else None,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
                message_count=len(messages),
                messages=[
                    ChatMessageResponse(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp.isoformat()
                    )
                    for msg in messages
                ]
            ))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"채팅 세션 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 지원자 정보 관련 API
# -----------------------------
@app.get(
    "/applicants/{applicant_id}",
    response_model=ApplicantResponse,
    tags=["Applicants"],
    summary="지원자 정보 조회",
    description="특정 지원자의 정보를 조회합니다."
)
async def get_applicant(applicant_id: int, db: Session = Depends(get_db)):
    """지원자 정보 조회"""
    try:
        applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {applicant_id}를 찾을 수 없습니다."
            )
        return applicant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"지원자 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


class ApplicantUpdateRequest(BaseModel):
    name: Optional[str] = None
    major: Optional[str] = None
    interest_keyword: Optional[str] = None
    learning_styles: Optional[List[str]] = None


@app.put(
    "/applicants/{applicant_id}",
    response_model=ApplicantResponse,
    tags=["Applicants"],
    summary="지원자 정보 수정",
    description="지원자의 정보를 수정합니다."
)
async def update_applicant(
    applicant_id: int,
    request: ApplicantUpdateRequest,
    db: Session = Depends(get_db)
):
    """지원자 정보 수정"""
    try:
        applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {applicant_id}를 찾을 수 없습니다."
            )
        
        # 입력 검증
        if request.interest_keyword:
            valid_keywords = ["디지털 전환", "조직 학습", "기술 혁신", "기술 전략", "지속가능경영"]
            if request.interest_keyword not in valid_keywords:
                raise HTTPException(
                    status_code=400,
                    detail=f"관심 키워드는 다음 중 하나여야 합니다: {', '.join(valid_keywords)}"
                )
        
        if request.learning_styles:
            valid_styles = ["사례 기반", "협업형", "탐구형", "자율형", "피드백 선호", "실증 분석"]
            for style in request.learning_styles:
                if style not in valid_styles:
                    raise HTTPException(
                        status_code=400,
                        detail=f"학습 성향은 다음 중 선택해야 합니다: {', '.join(valid_styles)}"
                    )
        
        # 정보 업데이트
        if request.name is not None:
            applicant.name = request.name
        if request.major is not None:
            applicant.major = request.major
        if request.interest_keyword is not None:
            applicant.interest_keyword = request.interest_keyword
        if request.learning_styles is not None:
            applicant.learning_styles = ", ".join(request.learning_styles)
        
        db.commit()
        db.refresh(applicant)
        
        return applicant
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"지원자 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 매칭 관련 API
# -----------------------------
@app.post(
    "/match",
    response_model=MatchingResponse,
    tags=["Matching"],
    summary="지원자-교수님 매칭 적합도 측정",
    description="""
    지원자와 교수님 간의 적합도를 5가지 지표(Indicator)를 기반으로 측정합니다.
    
    **측정 지표:**
    - A. 연구 키워드 (Research Keyword)
    - B. 연구 방법론 (Research Methodology)
    - C. 커뮤니케이션 (Communication)
    - D. 학문 접근도 (Academic Approach)
    - E. 교수 선호도 (Preferred Student Type)
    
    **입력값:**
    - **interest_keyword**: 관심 키워드 (필수)
      - 디지털 전환, 조직 학습, 기술 혁신, 기술 전략, 지속가능경영
    - **learning_styles**: 학습 성향 (필수, 여러 개 선택 가능)
      - 사례 기반, 협업형, 탐구형, 자율형, 피드백 선호, 실증 분석
    
    **응답:**
    - 각 교수님별로 5가지 지표의 점수와 최종 적합도 점수 제공
    - 매칭 근거 설명 포함
    - 지원자 정보는 자동으로 데이터베이스에 저장됨
    """
)
async def match_applicant(
    request: ApplicantRequest,
    professor_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    지원자와 교수님 간의 매칭 적합도 측정
    
    - **name**: 지원자 이름 (선택사항)
    - **major**: 전공 (선택사항)
    - **interest_keyword**: 관심 키워드 (1개 선택, 필수)
      - 디지털 전환, 조직 학습, 기술 혁신, 기술 전략, 지속가능경영
    - **learning_styles**: 학습 성향 (여러 개 선택 가능, 필수)
      - 사례 기반, 협업형, 탐구형, 자율형, 피드백 선호, 실증 분석
    - **professor_ids**: 특정 교수님 ID 리스트 (선택사항, 없으면 모든 교수님)
    
    **응답:**
    - **applicant_id**: 지원자 ID (항상 반환, 데이터베이스에 저장됨)
    - **results**: 각 교수님별 indicator별 매칭 점수와 전체 점수
      - **indicator_scores**: 각 indicator별 적합도 (100점 만점)
        - A. 연구 키워드 (Research Keyword)
        - B. 연구 방법론 (Research Methodology)
        - C. 커뮤니케이션 (Communication)
        - D. 학문 접근도 (Academic Approach)
        - E. 교수 선호도 (Preferred Student Type)
      - **total_score**: 최종 적합도 (70-98점, 정수)
      - **rationale**: 매칭 근거 설명
    """
    try:
        # 입력 검증
        valid_keywords = ["디지털 전환", "조직 학습", "기술 혁신", "기술 전략", "지속가능경영"]
        if request.interest_keyword not in valid_keywords:
            raise HTTPException(
                status_code=400,
                detail=f"관심 키워드는 다음 중 하나여야 합니다: {', '.join(valid_keywords)}"
            )
        
        valid_styles = ["사례 기반", "협업형", "탐구형", "자율형", "피드백 선호", "실증 분석"]
        for style in request.learning_styles:
            if style not in valid_styles:
                raise HTTPException(
                    status_code=400,
                    detail=f"학습 성향은 다음 중 선택해야 합니다: {', '.join(valid_styles)}"
                )
        
        # 지원자 데이터 준비
        applicant_data = {
            "interest_keyword": request.interest_keyword,
            "learning_styles": request.learning_styles
        }
        
        # 지원자 정보를 데이터베이스에 저장 (항상 저장)
        applicant = Applicant(
            name=request.name,
            major=request.major,
            interest_keyword=request.interest_keyword,
            learning_styles=", ".join(request.learning_styles),
            created_at=datetime.now().isoformat()
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
        
        # 매칭 점수 계산
        matching_results = match_all_professors(applicant_data, professor_ids)
        
        # 교수님 이름 추가 (매칭 근거는 별도 API로 분리)
        for result in matching_results:
            professor = db.query(Professor).filter(
                Professor.professor_id == result["professor_id"]
            ).first()
            if professor:
                result["professor_name"] = professor.name
        
        # 응답 형식 변환
        formatted_results = []
        for result in matching_results:
            formatted_results.append(MatchingResult(
                professor_id=result["professor_id"],
                professor_name=result.get("professor_name"),
                total_score=result["total_score"],
                indicator_scores=[
                    IndicatorScore(
                        indicator=ind["indicator"],
                        score=ind["score"],
                        qa_count=ind.get("qa_count", 0),
                        details=ind.get("details", [])
                    )
                    for ind in result["indicator_scores"]
                ],
                breakdown=result["breakdown"],
                rationale=None  # 초기 매칭에서는 근거 생성하지 않음 (별도 API 사용)
            ))
        
        return MatchingResponse(
            applicant_id=applicant.id,
            results=formatted_results,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"매칭 점수 계산 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 매칭 근거 생성 API (별도 엔드포인트)
# -----------------------------
class RationaleRequest(BaseModel):
    applicant_id: int
    professor_id: str


class RationaleResponse(BaseModel):
    rationale: str
    success: bool = True


@app.post(
    "/match/rationale",
    tags=["Matching"],
    summary="매칭 근거 생성 (SSE 스트리밍)",
    description="""
    특정 교수님과의 매칭 근거를 SSE(Server-Sent Events)로 스트리밍하여 생성합니다.
    
    **사용 시점:**
    - 초기 매칭 후 교수님을 선택했을 때
    - 상세한 매칭 근거가 필요할 때
    
    **주의:**
    - 초기 매칭(`/match`)에서는 근거가 포함되지 않습니다
    - 이 API를 호출하여 근거를 스트리밍으로 받으세요
    - SSE 형식으로 실시간 스트리밍됩니다
    
    **응답 형식 (SSE):**
    ```
    data: {"content": "텍스트 청크", "done": false}
    data: {"content": "텍스트 청크", "done": false}
    data: {"content": "", "done": true}
    ```
    """
)
async def get_matching_rationale_stream(
    request: RationaleRequest,
    db: Session = Depends(get_db)
):
    """
    매칭 근거 생성 (SSE 스트리밍)
    
    - **applicant_id**: 지원자 ID
    - **professor_id**: 교수님 ID
    
    Returns:
        SSE 스트리밍 응답
    """
    try:
        # 지원자 정보 조회
        applicant = db.query(Applicant).filter(Applicant.id == request.applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {request.applicant_id}를 찾을 수 없습니다."
            )
        
        # 교수님 정보 조회
        professor = db.query(Professor).filter(
            Professor.professor_id == request.professor_id
        ).first()
        if not professor:
            raise HTTPException(
                status_code=404,
                detail=f"교수님 ID {request.professor_id}를 찾을 수 없습니다."
            )
        
        # 지원자 데이터 준비
        applicant_data = {
            "interest_keyword": applicant.interest_keyword,
            "learning_styles": [s.strip() for s in applicant.learning_styles.split(",")]
        }
        
        # 매칭 점수 계산
        matching_result = calculate_matching_score(applicant_data, request.professor_id)
        
        # 매칭 근거 스트리밍 생성
        applicant_name = applicant.name if applicant.name else "지원자"
        
        from matching import generate_matching_rationale_stream
        
        def generate_stream():
            try:
                for chunk in generate_matching_rationale_stream(
                    applicant_name=applicant_name,
                    applicant_data=applicant_data,
                    professor_id=request.professor_id,
                    professor_name=professor.name,
                    matching_result=matching_result
                ):
                    yield chunk
            except Exception as e:
                # 오류 발생 시 오류 메시지 전송
                error_msg = json.dumps({
                    "content": f"오류가 발생했습니다: {str(e)}",
                    "done": True,
                    "error": True
                }, ensure_ascii=False)
                yield f"data: {error_msg}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"매칭 근거 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.post(
    "/match/final",
    response_model=FinalReportResponse,
    tags=["Matching"],
    summary="최종 적합도 리포트 생성",
    description="""
    채팅 내역을 포함한 최종 적합도 리포트를 생성합니다.
    
    **포함 내용:**
    - 1차 적합도 점수 (키워드 및 학습 성향 기반)
    - 채팅 기반 점수 (대화 내용 분석)
    - 최종 적합도 점수 (가중 평균)
    - 상세 리포트 및 분석 내용
    
    **사용 시점:**
    - 지원자가 교수님과 채팅을 완료한 후
    - 최종 매칭 결과를 확인하고 싶을 때
    """
)
async def generate_final_matching_report(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    채팅 내역을 포함한 최종 적합도 리포트 생성
    
    - **session_id**: 채팅 세션 ID
    
    Returns:
        최종 적합도 리포트 (1차 적합도 + 채팅 기반 분석)
    """
    try:
        # 채팅 세션 조회
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"세션 ID {session_id}를 찾을 수 없습니다."
            )
        
        # 지원자 정보 조회
        applicant = db.query(Applicant).filter(Applicant.id == session.applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {session.applicant_id}를 찾을 수 없습니다."
            )
        
        # 교수님 정보 조회
        professor = db.query(Professor).filter(
            Professor.professor_id == session.professor_id
        ).first()
        if not professor:
            raise HTTPException(
                status_code=404,
                detail=f"교수님 ID {session.professor_id}를 찾을 수 없습니다."
            )
        
        # 채팅 메시지 조회
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).all()
        
        # 지원자 데이터 준비
        applicant_data = {
            "interest_keyword": applicant.interest_keyword,
            "learning_styles": [s.strip() for s in applicant.learning_styles.split(",")]
        }
        
        # 1차 적합도 계산
        initial_matching = calculate_matching_score(applicant_data, session.professor_id)
        
        # 채팅 메시지를 딕셔너리 형식으로 변환
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 채팅 기반 점수 계산 (채팅이 없으면 0점)
        chat_based = calculate_chat_based_score(
            chat_messages=chat_messages,
            applicant_data=applicant_data,
            professor_id=session.professor_id
        )
        
        # 최종 점수 계산
        # 채팅이 없으면 1차 적합도만 사용 (채팅 점수 0일 때는 가중치 조정)
        if chat_based["chat_score"] == 0:
            # 채팅이 없으면 1차 적합도를 그대로 사용
            final_score_value = initial_matching["total_score"]
        else:
            # 채팅이 있으면 가중 평균 사용
            weighted_score_data = calculate_final_matching_score(
                initial_score=initial_matching["total_score"],
                chat_score=chat_based["chat_score"],
                chat_analysis=chat_based.get("analysis", "")
            )
            final_score_value = weighted_score_data["final_score"]
        
        # 최종 점수 데이터 구성
        final_score_data = {
            "final_score": final_score_value,
            "initial_score": initial_matching["total_score"],
            "chat_score": chat_based["chat_score"],
            "weighted_score": final_score_value,
            "chat_analysis": chat_based.get("analysis", "채팅 내역이 없습니다.")
        }
        
        # 최종 리포트 생성
        report = generate_final_report(
            applicant_name=applicant.name or "지원자",
            applicant_data=applicant_data,
            professor_id=session.professor_id,
            professor_name=professor.name,
            initial_matching=initial_matching,
            chat_based_score=chat_based,
            final_score=final_score_data,
            chat_messages=chat_messages
        )
        
        return FinalReportResponse(
            session_id=session.id,
            applicant_id=session.applicant_id,
            professor_id=session.professor_id,
            professor_name=professor.name,
            initial_score=initial_matching["total_score"],
            chat_score=chat_based["chat_score"],
            final_score=final_score_data["final_score"],
            report=report,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최종 리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.post(
    "/email/draft",
    tags=["Email"],
    summary="상담 요청 이메일 초안 생성 (SSE 스트리밍)",
    description="""
    교수님께 보낼 상담 요청 이메일의 초안을 SSE(Server-Sent Events)로 스트리밍하여 생성합니다.
    
    **응답 형식 (SSE):**
    ```
    data: {"content": "텍스트 청크", "done": false}
    data: {"content": "텍스트 청크", "done": false}
    data: {"content": "", "done": true}
    ```
    """
)
async def create_email_draft(
    request: EmailDraftRequest,
    db: Session = Depends(get_db)
):
    """
    상담 요청 이메일 초안 생성
    
    - **applicant_id**: 지원자 ID
    - **professor_id**: 교수님 ID
    - **session_id**: 채팅 세션 ID (선택사항, 최종 적합도 점수 포함 시)
    - **appointment_date**: 상담 희망 날짜 (예: "2025년 12월 17일")
    - **appointment_time**: 상담 희망 시간 (예: "오후 3시 12분")
    - **consultation_method**: 상담 방식 ("대면", "zoom", "전화")
    
    Returns:
        이메일 초안 텍스트
    """
    try:
        # 지원자 정보 조회
        applicant = db.query(Applicant).filter(Applicant.id == request.applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {request.applicant_id}를 찾을 수 없습니다."
            )
        
        # 교수님 정보 조회
        professor = db.query(Professor).filter(
            Professor.professor_id == request.professor_id
        ).first()
        if not professor:
            raise HTTPException(
                status_code=404,
                detail=f"교수님 ID {request.professor_id}를 찾을 수 없습니다."
            )
        
        # 대학원 정보 조회
        graduate_school = db.query(GraduateSchool).filter(
            GraduateSchool.id == professor.graduate_school_id
        ).first()
        if not graduate_school:
            raise HTTPException(
                status_code=404,
                detail=f"대학원 정보를 찾을 수 없습니다."
            )
        
        # 최종 적합도 점수 조회 (session_id가 제공된 경우)
        final_score = None
        if request.session_id:
            try:
                session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
                if session:
                    # 지원자 데이터 준비
                    applicant_data = {
                        "interest_keyword": applicant.interest_keyword,
                        "learning_styles": [s.strip() for s in applicant.learning_styles.split(",")]
                    }
                    
                    # 1차 적합도 계산
                    initial_matching = calculate_matching_score(applicant_data, request.professor_id)
                    
                    # 채팅 메시지 조회
                    messages = db.query(ChatMessage).filter(
                        ChatMessage.session_id == request.session_id
                    ).order_by(ChatMessage.timestamp).all()
                    
                    if messages:
                        # 채팅 메시지를 딕셔너리 형식으로 변환
                        chat_messages = [
                            {"role": msg.role, "content": msg.content}
                            for msg in messages
                        ]
                        
                        # 채팅 기반 점수 계산
                        chat_based = calculate_chat_based_score(
                            chat_messages=chat_messages,
                            applicant_data=applicant_data,
                            professor_id=request.professor_id
                        )
                        
                        # 최종 점수 계산
                        if chat_based["chat_score"] == 0:
                            final_score = initial_matching["total_score"]
                        else:
                            final_score_data = calculate_final_matching_score(
                                initial_score=initial_matching["total_score"],
                                chat_score=chat_based["chat_score"],
                                chat_analysis=chat_based.get("analysis", "")
                            )
                            final_score = final_score_data["final_score"]
                    else:
                        # 채팅이 없으면 1차 적합도만 사용
                        final_score = initial_matching["total_score"]
            except Exception as e:
                # 세션 조회 실패해도 이메일 초안은 생성 가능
                pass
        
        # 이메일 초안 스트리밍 생성
        from matching import generate_email_draft_stream
        
        def generate_stream():
            try:
                for chunk in generate_email_draft_stream(
                    applicant_name=applicant.name or "지원자",
                    applicant_major=applicant.major,
                    applicant_interest_keyword=applicant.interest_keyword,
                    graduate_school_name=graduate_school.name,
                    professor_name=professor.name,
                    professor_research_fields=professor.research_fields,
                    final_score=final_score,
                    appointment_date=request.appointment_date,
                    appointment_time=request.appointment_time,
                    consultation_method=request.consultation_method
                ):
                    yield chunk
            except Exception as e:
                # 오류 발생 시 오류 메시지 전송
                error_msg = json.dumps({
                    "content": f"오류가 발생했습니다: {str(e)}",
                    "done": True,
                    "error": True
                }, ensure_ascii=False)
                yield f"data: {error_msg}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이메일 초안 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.post(
    "/email/send",
    response_model=EmailSendResponse,
    tags=["Email"],
    summary="상담 요청 이메일 전송",
    description="생성된 이메일 초안을 교수님께 실제로 전송합니다."
)
async def send_consultation_email(
    request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """
    상담 요청 이메일 전송
    
    - **applicant_id**: 지원자 ID
    - **professor_id**: 교수님 ID
    - **email_subject**: 이메일 제목
    - **email_body**: 이메일 본문 (초안)
    - **from_email**: 발신자 이메일 (선택사항, 기본값: 환경 변수 값)
    - **from_name**: 발신자 이름 (선택사항, 기본값: 환경 변수 값)
    
    Returns:
        이메일 전송 결과
    """
    try:
        # 지원자 정보 조회
        applicant = db.query(Applicant).filter(Applicant.id == request.applicant_id).first()
        if not applicant:
            raise HTTPException(
                status_code=404,
                detail=f"지원자 ID {request.applicant_id}를 찾을 수 없습니다."
            )
        
        # 교수님 정보 조회
        professor = db.query(Professor).filter(
            Professor.professor_id == request.professor_id
        ).first()
        if not professor:
            raise HTTPException(
                status_code=404,
                detail=f"교수님 ID {request.professor_id}를 찾을 수 없습니다."
            )
        
        # 교수님 이메일 주소 확인
        if not professor.email:
            raise HTTPException(
                status_code=400,
                detail=f"{professor.name} 교수님의 이메일 주소가 등록되어 있지 않습니다."
            )
        
        # 이메일 전송
        result = send_email(
            to_email=professor.email,
            subject=request.email_subject,
            body=request.email_body,
            from_email=request.from_email,
            from_name=request.from_name
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )
        
        return EmailSendResponse(
            success=True,
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이메일 전송 중 오류가 발생했습니다: {str(e)}"
        )


# -----------------------------
# 서버 실행
# -----------------------------
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload  # 개발 모드: 코드 변경 시 자동 재시작
    )

