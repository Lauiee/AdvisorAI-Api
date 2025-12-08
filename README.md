# 학생-교수 트윈 MVP API

FastAPI 기반의 학생-교수 매칭 및 교수 트윈 AI 채팅 시스템입니다.

## 기술 스택

- Python 3.11
- FastAPI
- OpenAI API (text-embedding-3-small, gpt-4o-mini)
- NumPy, scikit-learn

## 주요 기능

1. **적합도 계산** (`POST /match`)
   - 학생 키워드와 교수 키워드 매칭
   - 키워드 기반 적합도 점수 계산 (0~1)

2. **교수 트윈 채팅** (`POST /chat`)
   - RAG 기반 질의응답
   - 학생 질문에 대해 관련된 교수 QA를 검색하여 답변 생성

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY를 설정
```

또는 환경 변수로 직접 설정:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 서버 실행

```bash
python main.py
```

또는 uvicorn으로 직접 실행:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 `http://localhost:8000`에서 접근할 수 있습니다.

### 4. API 문서 확인

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API 사용 예시

### 1. 적합도 계산 (`POST /match`)

**요청:**
```bash
curl -X POST "http://localhost:8000/match" \
  -H "Content-Type: application/json" \
  -d '{
    "student_keywords": ["인공지능", "머신러닝", "연구", "논문"]
  }'
```

**응답:**
```json
{
  "fitness_score": 0.8,
  "keyword_match_score": 0.8,
  "qa_similarity_score": null,
  "message": "적합도 점수: 0.800 (키워드 매칭: 0.800)"
}
```

### 2. 교수 트윈 채팅 (`POST /chat`)

**요청:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "연구실에 학부생도 참여할 수 있나요?"
  }'
```

**응답:**
```json
{
  "answer": "네, 학부생도 연구에 참여할 수 있습니다. 관심 있는 학생은 이메일로 문의해주세요. 연구실에서는 다양한 프로젝트를 통해 실무 경험을 쌓을 수 있는 기회를 제공합니다.",
  "relevant_qa": [
    {
      "question": "학부생도 연구에 참여할 수 있나요?",
      "answer": "네, 학부생도 연구에 참여할 수 있습니다. 관심 있는 학생은 이메일로 문의해주세요.",
      "similarity_score": 0.95
    },
    {
      "question": "연구실 분위기는 어떤가요?",
      "answer": "협력적이고 열린 분위기입니다. 정기적인 미팅과 토론을 통해 함께 성장합니다.",
      "similarity_score": 0.72
    },
    {
      "question": "연구 주제는 어떻게 정하나요?",
      "answer": "최신 논문을 읽고, 관심 있는 분야를 탐색하며, 교수님과 상의하여 결정합니다.",
      "similarity_score": 0.68
    }
  ]
}
```

## Python 코드로 테스트

```python
import requests

# 적합도 계산
match_response = requests.post(
    "http://localhost:8000/match",
    json={
        "student_keywords": ["인공지능", "머신러닝", "연구"]
    }
)
print("적합도:", match_response.json())

# 채팅
chat_response = requests.post(
    "http://localhost:8000/chat",
    json={
        "question": "대학원 생활은 어떤가요?"
    }
)
print("답변:", chat_response.json()["answer"])
```

## 프로젝트 구조

```
AdvisorAI-Api/
├── main.py              # FastAPI 서버 및 엔드포인트
├── models.py            # 교수 트윈 모델 로직
├── requirements.txt     # 의존성 목록
├── .env.example        # 환경 변수 예시
└── README.md           # 프로젝트 문서
```

## 주요 모델 및 함수

### `models.py`

- `ProfessorTwinModel`: 교수 트윈 모델 클래스
  - `generate_embeddings()`: 텍스트 임베딩 생성
  - `load_professor_data()`: 교수 QA 데이터 로드 및 임베딩 생성
  - `calculate_keyword_match_score()`: 키워드 매칭 점수 계산
  - `calculate_qa_similarity()`: QA 유사도 계산
  - `calculate_fitness_score()`: 종합 적합도 점수 계산
  - `search_relevant_qa()`: 관련 QA 검색
  - `generate_rag_response()`: RAG 기반 응답 생성

### `main.py`

- `POST /match`: 적합도 점수 계산 엔드포인트
- `POST /chat`: 교수 트윈 채팅 엔드포인트
- `GET /health`: 헬스 체크 엔드포인트

## 샘플 데이터

프로젝트에는 20개의 교수 QA 샘플 데이터가 포함되어 있습니다:
- 연구 분야, 학부생 연구 참여, 공부 방법, 대학원 생활 등 다양한 주제

## 주의사항

1. OpenAI API 키가 필요합니다. [OpenAI Platform](https://platform.openai.com/)에서 발급받을 수 있습니다.
2. API 사용량에 따라 비용이 발생할 수 있습니다.
3. 첫 실행 시 교수 QA 임베딩 생성에 시간이 걸릴 수 있습니다 (약 10-20초).

## 라이선스

MIT

