# AI Adviser 프로젝트 구현 상태 문서

## 📋 프로젝트 개요

AI Adviser는 대학원생들이 교수님의 연구 스타일과 지도 방식을 파악할 수 있도록 도와주는 RAG(Retrieval-Augmented Generation) 기반 AI 시스템입니다.

---

## 🏗️ 프로젝트 구조

```
ai-adviser/
├── api.py                 # FastAPI 서버 및 API 엔드포인트
├── chat.py                # RAG 기반 대화 로직
├── embadding.py           # 데이터 임베딩 및 Pinecone 업로드
├── database.py            # SQLAlchemy 데이터베이스 모델
├── db_init.py             # 데이터베이스 초기화 스크립트
├── add_data.py            # 대학원/교수님 데이터 추가 도구
├── professor_data.json    # 교수님 Q&A 데이터 (Pinecone용)
├── ai_adviser.db          # SQLite 데이터베이스 파일
└── IMPLEMENTATION_STATUS.md  # 본 문서
```

---

## ✅ 구현 완료 기능

### 1. 데이터 임베딩 및 벡터 저장소 구축

**파일:** `embadding.py`

- **기능:**
  - 교수님 프로필 및 Q&A 데이터를 JSON에서 읽어옴
  - OpenAI `text-embedding-3-small` 모델로 임베딩 생성
  - Pinecone 벡터 데이터베이스에 저장
  - Q&A 타입 데이터는 질문과 답변을 함께 임베딩하여 검색 품질 향상

- **데이터 구조:**
  - 프로필 정보 (5개 항목)
  - Q&A 정보 (20개 항목)
  - 총 24개 벡터 저장

- **메타데이터:**
  - `professor_id`: 교수님 ID
  - `chunk_id`: 청크 고유 ID
  - `type`: 데이터 타입 (profile/qa)
  - `question`, `answer`: Q&A 정보
  - `title`, `text`: 프로필 정보

### 2. RAG 기반 대화 시스템

**파일:** `chat.py`

- **핵심 기능:**
  - 사용자 질문을 임베딩하여 Pinecone에서 유사한 정보 검색
  - 검색된 정보를 컨텍스트로 활용하여 LLM이 답변 생성
  - 교수님이 직접 답변하는 형식 (1인칭)으로 응답

- **주요 함수:**
  - `embed_text()`: 텍스트 임베딩 생성
  - `search_similar_chunks()`: Pinecone에서 유사 벡터 검색
  - `format_context()`: 검색 결과를 컨텍스트로 변환
  - `generate_answer()`: RAG 기반 답변 생성
  - `chat_loop()`: 대화형 인터페이스

- **프롬프트 특징:**
  - 교수님의 입장에서 직접 답변 (1인칭)
  - 제공된 정보만을 사용하여 답변 (추측 방지)
  - 친절하고 명확한 답변 스타일

### 3. FastAPI REST API

**파일:** `api.py`

#### 구현된 API 엔드포인트

##### 3.1 헬스 체크
- `GET /`: API 상태 확인
- `GET /health`: 헬스 체크

##### 3.2 RAG 대화 API
- `POST /chat`
  - **요청:**
    ```json
    {
      "question": "교수님은 어떤 연구 방법론을 선호하시나요?",
      "top_k": 3
    }
    ```
  - **응답:**
    ```json
    {
      "answer": "저는 개인적으로 정성적 분석...",
      "references": ["- 연구 방법론은 어떤 방식을 선호하시나요?", ...],
      "success": true
    }
    ```

##### 3.3 대학원/교수님 정보 API
- `GET /graduate-schools`
  - 모든 대학원 목록 조회
  - **응답:**
    ```json
    [
      {
        "id": 1,
        "name": "서강대학교 기술경영전문대학원",
        "description": "..."
      }
    ]
    ```

- `GET /graduate-schools/{school_id}/professors`
  - 특정 대학원의 교수님 목록과 기본 정보 조회
  - **응답:**
    ```json
    {
      "graduate_school": {
        "id": 1,
        "name": "...",
        "description": "..."
      },
      "professors": [
        {
          "id": 1,
          "professor_id": "prof_001",
          "name": "박현규",
          "major": "기술경영학",
          "research_fields": "...",
          "introduction": "...",
          "education": "...",
          "career": "...",
          "courses": "..."
        }
      ],
      "total_count": 1
    }
    ```

### 4. 데이터베이스 구조

**파일:** `database.py`

#### 테이블 구조

**GraduateSchool (대학원)**
- `id`: Primary Key
- `name`: 대학원 이름 (Unique)
- `description`: 대학원 설명

**Professor (교수님)**
- `id`: Primary Key
- `professor_id`: 외부 ID (prof_001 등, Unique)
- `name`: 교수님 이름
- `graduate_school_id`: Foreign Key (GraduateSchool.id)
- `major`: 전공
- `research_fields`: 연구 분야
- `introduction`: 소개
- `education`: 학력
- `career`: 경력
- `courses`: 담당 과목

### 5. 데이터 관리 도구

**파일:** `add_data.py`

- 대학원 추가
- 교수님 정보 추가
- 대학원 목록 조회
- 인터랙티브 CLI 인터페이스

---

## 🔧 기술 스택

### 백엔드
- **FastAPI**: REST API 프레임워크
- **SQLAlchemy**: ORM (SQLite 사용)
- **Uvicorn**: ASGI 서버

### AI/ML
- **OpenAI API**: 
  - `text-embedding-3-small`: 텍스트 임베딩
  - `gpt-4o-mini`: 답변 생성
- **Pinecone**: 벡터 데이터베이스

### 데이터베이스
- **SQLite**: 관계형 데이터베이스 (대학원/교수님 정보)
- **Pinecone**: 벡터 데이터베이스 (RAG 검색용)

---

## 📦 설치 및 실행

### 1. 패키지 설치

```bash
pip3 install fastapi uvicorn sqlalchemy openai pinecone-client tqdm
```

### 2. 데이터베이스 초기화

```bash
python3 db_init.py
```

### 3. 데이터 임베딩 및 업로드

```bash
python3 embadding.py
```

### 4. API 서버 실행

```bash
python3 api.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

### 5. API 문서 확인

브라우저에서 `http://localhost:8000/docs` 접속하여 Swagger UI에서 API를 테스트할 수 있습니다.

---

## 📝 데이터 관리

### 데이터 추가

```bash
python3 add_data.py
```

1. 대학원 추가
2. 교수님 정보 추가
3. 대학원 목록 조회

### 데이터 구조

**Pinecone 데이터 (`professor_data.json`):**
- 교수님 프로필 정보
- Q&A 데이터 (20개 항목)
- RAG 검색에 사용

**SQLite 데이터 (`ai_adviser.db`):**
- 대학원 정보
- 교수님 기본 정보
- API 조회에 사용

---

## 🎯 현재 구현 상태 요약

### ✅ 완료된 기능
1. ✅ 데이터 임베딩 및 Pinecone 저장
2. ✅ RAG 기반 대화 시스템
3. ✅ FastAPI REST API
4. ✅ 대학원/교수님 정보 조회 API
5. ✅ 데이터베이스 구조 및 관리 도구
6. ✅ 교수님 직접 답변 형식 (1인칭)

### 🔄 향후 개발 예정
- [ ] 교수님별 채팅 세션 관리
- [ ] 대화 히스토리 저장
- [ ] 사용자 인증 및 권한 관리
- [ ] 프론트엔드 연동
- [ ] 추가 대학원/교수님 데이터 확장

---

## 🔑 API 키 설정

현재 코드에 하드코딩된 API 키들이 있습니다. 프로덕션 환경에서는 환경 변수로 관리하는 것을 권장합니다.

**필요한 API 키:**
- OpenAI API Key
- Pinecone API Key

---

## 📊 테스트 결과

### RAG 시스템 정확도
- ✅ 데이터 기반 정확한 답변 생성 확인
- ✅ 교수님의 실제 답변 스타일 반영
- ✅ 관련 정보 검색 정확도 우수

### API 동작 확인
- ✅ 모든 엔드포인트 정상 작동
- ✅ CORS 설정 완료
- ✅ 에러 처리 구현

---

## 📞 문의 및 지원

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**최종 업데이트:** 2024년 12월
**버전:** 1.0.0

