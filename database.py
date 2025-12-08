from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Generator
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_adviser.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite용
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# -----------------------------
# 데이터베이스 모델
# -----------------------------
class GraduateSchool(Base):
    """대학원 테이블"""
    __tablename__ = "graduate_schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # 대학원 명
    education_fields = Column(Text, nullable=True)  # 대학원 교육 분야 (예: 기술경영, 기술혁신)
    keywords = Column(Text, nullable=True)  # 키워드 (예: 기술 전략, AI전환, 창업)
    
    # 관계 설정
    professors = relationship("Professor", back_populates="graduate_school")


class Professor(Base):
    """교수님 테이블"""
    __tablename__ = "professors"
    
    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(String(50), unique=True, nullable=False, index=True)  # 외부 ID (prof_001 등)
    name = Column(String(100), nullable=False)  # 교수님 이름
    graduate_school_id = Column(Integer, ForeignKey("graduate_schools.id"), nullable=False)
    
    # 기본 정보
    major = Column(String(100), nullable=True)  # 전공
    research_fields = Column(Text, nullable=True)  # 연구 분야
    introduction = Column(Text, nullable=True)  # 소개
    education = Column(Text, nullable=True)  # 학력
    career = Column(Text, nullable=True)  # 경력
    courses = Column(Text, nullable=True)  # 담당 과목
    email = Column(String(200), nullable=True)  # 이메일 주소
    
    # 관계 설정
    graduate_school = relationship("GraduateSchool", back_populates="professors")


class Applicant(Base):
    """지원자 테이블"""
    __tablename__ = "applicants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # 지원자 이름
    major = Column(String(100), nullable=True)  # 전공
    interest_keyword = Column(String(100), nullable=False)  # 관심 키워드
    learning_styles = Column(Text, nullable=False)  # 학습 성향 (쉼표로 구분)
    created_at = Column(String(50), nullable=True)  # 생성 시간
    
    # 관계 설정
    chat_sessions = relationship("ChatSession", back_populates="applicant")


class ChatSession(Base):
    """채팅 세션 테이블"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False, index=True)
    professor_id = Column(String(50), nullable=False, index=True)  # professor_id (prof_001 등)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계 설정
    applicant = relationship("Applicant", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """채팅 메시지 테이블"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" 또는 "professor"
    content = Column(Text, nullable=False)  # 메시지 내용
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")


# -----------------------------
# 데이터베이스 초기화
# -----------------------------
def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)


# -----------------------------
# 데이터베이스 세션 의존성
# -----------------------------
def get_db() -> Generator:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

