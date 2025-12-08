# AI Adviser 서비스 시퀀스 및 구현 현황

## 현재 구현된 API 엔드포인트

### 헬스 체크

- `GET /`: API 상태 확인
- `GET /health`: 헬스 체크

### 대학원/교수님 정보

- `GET /graduate-schools`: 모든 대학원 목록 조회
- `GET /graduate-schools/{school_id}/professors`: 특정 대학원의 교수님 목록 조회

### 지원자 정보 관련

- `GET /applicants/{applicant_id}`: 지원자 정보 조회
- `PUT /applicants/{applicant_id}`: 지원자 정보 수정

### 채팅 관련

- `POST /chat`: 교수님과의 RAG 기반 대화 (세션 ID 포함 시 메시지 자동 저장)
- `POST /chat/session`: 채팅 세션 생성
- `GET /chat/session/{session_id}`: 채팅 세션 조회
- `GET /chat/sessions/applicant/{applicant_id}`: 지원자의 모든 채팅 세션 조회

### 매칭 관련

- `POST /match`: 지원자와 교수님 간의 1차 매칭 적합도 측정 (지원자 정보 저장 포함)
- `POST /match/final?session_id={session_id}`: 채팅 내역 포함 최종 적합도 리포트 생성

### 이메일 관련

- `POST /email/draft`: 상담 요청 이메일 초안 생성
- `POST /email/send`: 상담 요청 이메일 전송

---

## 서비스 시퀀스

### 1. 원하는 대학원 선택

**상태:** ✅ **완료**

**구현 내용:**

- `GET /graduate-schools`: 모든 대학원 목록 조회
- `GET /graduate-schools/{school_id}/professors`: 특정 대학원의 교수님 목록 조회

**데이터 구조:**

- 대학원 정보: 이름, 교육 분야, 키워드
- 교수님 기본 정보: 이름, 전공, 연구 분야, 소개, 학력, 경력, 담당 과목

---

### 2. 지원자 정보 입력

**상태:** ✅ **완료**

**구현 내용:**

- `POST /match` 엔드포인트에서 지원자 정보를 받음
  - 이름 (선택사항)
  - 전공 (선택사항) ✅ 추가됨
  - 관심 키워드 (필수)
  - 학습 성향 (필수, 다중 선택)
- 지원자 정보는 항상 데이터베이스에 저장됨 ✅
- `applicant_id`가 항상 반환됨 ✅

**추가 API:**

- `GET /applicants/{applicant_id}`: 지원자 정보 조회
- `PUT /applicants/{applicant_id}`: 지원자 정보 수정
  - 이름, 전공, 관심 키워드, 학습 성향 수정 가능

---

### 3. 지원자 정보 기반 각 교수별 적합도 1차 추출

**상태:** ✅ **완료**

**구현 내용:**

- `POST /match`: 지원자와 모든 교수님 간의 매칭 점수 계산
- **응답 내용:**
  - 최종 적합도 (70-98점, 정수)
  - Indicator별 적합도 (A-E, 각 100점 만점)
    - A. 연구 키워드 (Research Keyword)
    - B. 연구 방법론 (Research Methodology)
    - C. 커뮤니케이션 (Communication)
    - D. 학문 접근도 (Academic Approach)
    - E. 교수 선호도 (Preferred Student Type)
  - 매칭 근거 (rationale): AI가 생성한 상세 설명

**기술 스택:**

- OpenAI Embeddings (text-embedding-3-small)
- 코사인 유사도 계산
- GPT-4o-mini를 사용한 근거 생성

---

### 4. 지원자는 교수들 중 원하는 교수와 채팅 시뮬레이션 시작

**상태:** ✅ **완료**

**구현 내용:**

- `POST /chat`: 교수님과의 RAG 기반 대화
- **요청:**
  - `question`: 사용자 질문
  - `professor_id`: 교수님 ID (필수)
  - `top_k`: 검색할 관련 정보 개수 (기본값: 3)
- **응답:**
  - `answer`: 교수님의 답변 (1인칭)
  - `references`: 참조된 질문/답변 목록

**특징:**

- 교수님별로 필터링된 RAG 검색
- 자기소개 질문 시 프로필 정보 우선 검색
- 교수님 이름을 동적으로 주입하여 개인화된 답변

---

### 5. 교수(twin)과 채팅 시뮬레이션 진행 후 채팅 내역까지 포함한 최종 적합도 추출

**상태:** ✅ **완료**

**구현 내용:**

- **채팅 세션 관리:**

  - `POST /chat/session`: 채팅 세션 생성 (지원자 ID, 교수님 ID)
    - 기존 세션이 있으면 자동으로 반환
    - 세션 ID 반환
  - `GET /chat/session/{session_id}`: 채팅 세션 조회
  - `GET /chat/sessions/applicant/{applicant_id}`: 지원자의 모든 채팅 세션 조회

- **채팅 메시지 저장:**

  - `POST /chat` API에 `session_id` 포함 시 자동 저장
  - 질문과 답변이 자동으로 데이터베이스에 저장됨

- **채팅 내역 기반 적합도 계산:**

  - 대화 내용 분석 (GPT-4o-mini 사용)
  - 대화 품질, 호흡, 관심도, 관련성 평가
  - 채팅 기반 점수 계산 (70-98점)

- **최종 적합도 계산:**

  - 1차 적합도(60%) + 채팅 기반 점수(40%) 가중 평균
  - 채팅이 없으면 1차 적합도만 사용

- **최종 리포트 생성:**
  - `POST /match/final?session_id={session_id}`: 최종 리포트 생성
  - 1차 적합도 요약
  - 채팅 기반 분석 (채팅이 있는 경우)
  - 종합 평가 및 추천 사항
  - 리포트 형식 (텍스트)

**데이터베이스:**

- `ChatSession` 테이블: 채팅 세션 정보
- `ChatMessage` 테이블: 채팅 메시지 저장

**특징:**

- 채팅이 없어도 리포트 생성 가능 (1차 적합도만 사용)
- 채팅이 있으면 자동으로 분석하여 점수에 반영

---

### 6. 해당 교수님과 상담 예약을 원한다면 진행 혹은 다른 교수님 재탐색 가능

**상태:** ✅ **완료**

**구현 내용:**

- **다른 교수님 재탐색 기능:**

  - 최종 적합도 리포트 확인 후 다른 교수님 선택 가능
  - `POST /chat/session`: 새로운 교수님과 채팅 세션 생성
  - 새로운 교수님과 대화 시작 → 최종 적합도 확인 반복 가능
  - `GET /chat/sessions/applicant/{applicant_id}`: 지원자가 채팅한 모든 교수님 목록 조회 (참고용)

- **상담 예약 진행:**
  - 예약 시스템은 별도로 관리하지 않음
  - 이메일 전송이 곧 예약을 잡는 것으로 간주
  - 예약 날짜/시간 선택 후 이메일 전송 (7번 기능)

**시퀀스:**

1. 교수님 A와 대화 → 최종 적합도 리포트 확인
2. 만족스럽지 않으면 → 교수님 B 선택
3. `POST /chat/session`으로 교수님 B와 새 세션 생성
4. 교수님 B와 대화 → 최종 적합도 리포트 확인
5. 반복 가능

---

### 7. 상담 예약은 원하는 날짜와 시간을 고르고 교수님 이메일로 전송

**상태:** ✅ **완료**

**구현 내용:**

- `POST /email/send`: 이메일 전송 API
  - **요청:**
    - `applicant_id`: 지원자 ID
    - `professor_id`: 교수님 ID
    - `email_subject`: 이메일 제목
    - `email_body`: 이메일 본문 (초안)
    - `from_email`: 발신자 이메일 (선택사항)
    - `from_name`: 발신자 이름 (선택사항)
  - **응답:**
    - `success`: 전송 성공 여부
    - `message`: 결과 메시지

**기능:**

- SMTP를 사용한 이메일 전송 (Python `smtplib` 사용)
- 교수님 이메일 주소를 데이터베이스에서 자동 조회
- TLS 암호화 지원
- UTF-8 인코딩 지원 (한글 제목/본문)
- 에러 처리 및 상세한 오류 메시지 제공

**SMTP 설정:**

- 환경 변수로 SMTP 서버 설정 관리
- Gmail, Outlook, 네이버 등 다양한 이메일 서비스 지원
- 상세한 설정 가이드: `EMAIL_SETUP.md` 참고

**필요 환경 변수:**

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Advisor.AI
```

**사용 시퀀스:**

1. `POST /email/draft`: 이메일 초안 생성
2. 사용자가 초안 확인 및 수정 (선택사항)
3. `POST /email/send`: 이메일 전송

---

### 8. 이때 이메일 초안을 AI가 작성해 줄 수 있음

**상태:** ✅ **완료**

**구현 내용:**

- `POST /email/draft`: 이메일 초안 생성 API
  - **요청:**
    - `applicant_id`: 지원자 ID
    - `professor_id`: 교수님 ID
    - `session_id`: 채팅 세션 ID (선택사항, 최종 적합도 점수 포함 시)
    - `appointment_date`: 상담 희망 날짜 (예: "2025년 12월 17일")
    - `appointment_time`: 상담 희망 시간 (예: "오후 3시 12분")
    - `consultation_method`: 상담 방식 ("대면", "zoom", "전화")
  - **응답:**
    - `email_draft`: 생성된 이메일 초안 텍스트

**기능:**

- GPT-4o-mini를 사용한 AI 기반 이메일 초안 생성
- 지원자 정보 (이름, 전공, 관심 키워드) 포함
- 교수님 정보 (이름, 연구 분야) 포함
- 최종 적합도 점수 포함 (session_id 제공 시)
- 대학원 정보 포함
- 예약 요청 내용 (날짜, 시간, 상담 방식) 포함
- 정중하고 격식 있는 문체로 작성
- 예시 형식에 맞춘 구조화된 이메일

**특징:**

- `session_id`가 제공되면 해당 세션의 최종 적합도 점수를 이메일에 포함
- `session_id`가 없으면 적합도 없이 초안 생성
- 사용자가 수정 가능한 텍스트 형식으로 반환

---

## 전체 구현 현황 요약

| 단계 | 기능             | 상태    | 완성도 |
| ---- | ---------------- | ------- | ------ |
| 1    | 대학원 선택      | ✅ 완료 | 100%   |
| 2    | 지원자 정보 입력 | ✅ 완료 | 100%   |
| 3    | 1차 적합도 추출  | ✅ 완료 | 100%   |
| 4    | 채팅 시뮬레이션  | ✅ 완료 | 100%   |
| 5    | 최종 적합도 추출 | ✅ 완료 | 100%   |
| 6    | 상담 예약/재탐색 | ✅ 완료 | 100%   |
| 7    | 이메일 전송      | ✅ 완료 | 100%   |
| 8    | 이메일 초안 작성 | ✅ 완료 | 100%   |

**전체 진행률: 100%** (8개 기능 모두 완료)

---

## 구현 완료된 기능 요약

### ✅ 모든 핵심 기능 구현 완료

1. **대학원 선택** - 완료
2. **지원자 정보 입력** - 완료
3. **1차 적합도 추출** - 완료
4. **채팅 시뮬레이션** - 완료
5. **최종 적합도 추출** - 완료
6. **상담 예약/재탐색** - 완료
7. **이메일 전송** - 완료 (SMTP 구현)
8. **이메일 초안 작성** - 완료

## 추가 개선 가능 사항 (선택사항)

### 향후 개선 가능한 기능

1. **이메일 첨부파일 지원**

   - 최종 리포트 PDF 첨부
   - 지원자 이력서 첨부

2. **예약 관리 시스템**

   - 교수님별 예약 가능 시간대 관리
   - 예약 일정 확인 및 중복 방지

3. **이메일 템플릿 관리**
   - 다양한 이메일 템플릿 제공
   - 사용자 정의 템플릿 저장

---

## 기술 스택 현황

### 이미 사용 중

- FastAPI (REST API)
- SQLite + SQLAlchemy (데이터베이스)
- OpenAI API (Embeddings, GPT-4o-mini)
- Pinecone (벡터 데이터베이스)
- Uvicorn (ASGI 서버)

### 추가 필요

- 이메일 전송: `smtplib` 또는 외부 서비스 (SendGrid, Mailgun)
- 리포트 생성: `reportlab` (PDF) 또는 `jinja2` (HTML) - 현재는 텍스트 형식
- 예약 시스템: 추가 데이터베이스 테이블

---

## 데이터베이스 스키마

### ✅ 구현 완료

#### ChatSession 테이블

- id (PK)
- applicant_id (FK)
- professor_id (String)
- created_at (DateTime)
- updated_at (DateTime)

#### ChatMessage 테이블

- id (PK)
- session_id (FK)
- role (String: "user" 또는 "professor")
- content (Text)
- timestamp (DateTime)

#### Applicant 테이블

- id (PK)
- name (String, nullable)
- major (String, nullable) ✅ 추가됨
- interest_keyword (String)
- learning_styles (Text)
- created_at (String)

### 추가 필요

### Professor 테이블 확장

```sql
- email (VARCHAR(200), nullable) ✅ 추가 완료 - 이메일 전송을 위해 필수
- availability (선택사항) - 예약 가능 시간 관리용 (미구현)
```

**참고:** 예약 데이터는 별도 테이블로 관리하지 않음. 이메일 전송이 곧 예약으로 간주됨.
