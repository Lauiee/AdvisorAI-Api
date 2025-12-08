# API 사용 가이드

## 전체 서비스 흐름

### 1단계: 지원자 정보 입력 및 1차 매칭
**API:** `POST /match`

```json
{
  "name": "이서강",
  "interest_keyword": "기술 혁신",
  "learning_styles": ["자율형", "탐구형"]
}
```

**응답:**
- `applicant_id`: 지원자 ID (저장됨)
- `results`: 각 교수님별 1차 적합도 점수와 근거

---

### 2단계: 채팅 세션 생성
**API:** `POST /chat/session`

```json
{
  "applicant_id": 1,
  "professor_id": "prof_001"
}
```

**응답:**
- `id`: 세션 ID (이걸 저장해야 함!)
- `applicant_id`: 지원자 ID
- `professor_id`: 교수님 ID
- `professor_name`: 교수님 이름
- `message_count`: 현재 메시지 개수
- `messages`: 기존 메시지들 (있으면)

**중요:** 
- 같은 지원자-교수님 조합으로 다시 호출하면 기존 세션을 반환합니다
- 세션 ID를 프론트엔드에 저장해두세요

---

### 3단계: 채팅 진행
**API:** `POST /chat`

```json
{
  "question": "교수님, 연구 방법론은 어떤 방식을 선호하시나요?",
  "professor_id": "prof_001",
  "session_id": 1,
  "top_k": 3
}
```

**응답:**
- `answer`: 교수님의 답변
- `references`: 참조된 질문들
- `session_id`: 세션 ID (확인용)

**중요:**
- `session_id`를 넣으면 자동으로 메시지가 저장됩니다
- `professor_id`는 필수입니다
- 여러 번 호출하면 대화가 누적됩니다

---

### 4단계: 채팅 내역 조회 (선택사항)
**API:** `GET /chat/session/{session_id}`

채팅 내역을 다시 불러올 때 사용합니다.

---

### 5단계: 최종 리포트 생성
**API:** `POST /match/final?session_id={session_id}`

**응답:**
- `initial_score`: 1차 적합도 점수
- `chat_score`: 채팅 기반 점수
- `final_score`: 최종 적합도 점수 (1차 60% + 채팅 40%)
- `report`: 상세 리포트 내용
- `chat_analysis`: 채팅 분석 결과

---

## 프론트엔드 구현 예시

### React 예시

```javascript
// 1. 지원자 정보 입력 및 1차 매칭
const submitApplicantInfo = async (applicantData) => {
  const response = await fetch('/match', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(applicantData)
  });
  const data = await response.json();
  // data.applicant_id 저장
  // data.results에 교수님별 점수
  return data;
};

// 2. 교수님 선택 후 채팅 세션 생성
const createChatSession = async (applicantId, professorId) => {
  const response = await fetch('/chat/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      applicant_id: applicantId,
      professor_id: professorId
    })
  });
  const data = await response.json();
  // data.id (세션 ID) 저장
  return data;
};

// 3. 채팅 메시지 전송
const sendMessage = async (question, professorId, sessionId) => {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question,
      professor_id: professorId,
      session_id: sessionId
    })
  });
  const data = await response.json();
  return data;
};

// 4. 최종 리포트 생성
const generateFinalReport = async (sessionId) => {
  const response = await fetch(`/match/final?session_id=${sessionId}`, {
    method: 'POST'
  });
  const data = await response.json();
  return data;
};
```

---

## 전체 플로우 다이어그램

```
[사용자]
  ↓
1. 지원자 정보 입력
  ↓
[POST /match]
  → applicant_id 받음
  → 교수님별 1차 적합도 확인
  ↓
2. 교수님 선택
  ↓
[POST /chat/session]
  → session_id 받음 (저장!)
  ↓
3. 채팅 시작
  ↓
[POST /chat] (반복)
  - question: "질문"
  - professor_id: "prof_001"
  - session_id: 1 (위에서 받은 ID)
  → answer 받음
  → 메시지 자동 저장됨
  ↓
4. 채팅 종료 후 리포트 생성
  ↓
[POST /match/final?session_id=1]
  → 최종 리포트 받음
  → 1차 점수 + 채팅 점수 종합
```

---

## 주요 포인트

1. **세션 ID는 반드시 저장하세요**
   - 채팅 세션 생성 후 받은 `id`를 프론트엔드 상태에 저장
   - 모든 채팅 메시지 전송 시 `session_id` 포함

2. **세션은 자동으로 재사용됩니다**
   - 같은 지원자-교수님 조합으로 세션 생성 API를 다시 호출하면
   - 기존 세션을 반환하므로 안전합니다

3. **메시지는 자동 저장됩니다**
   - `session_id`를 포함해서 `/chat` API를 호출하면
   - 질문과 답변이 자동으로 데이터베이스에 저장됩니다

4. **최종 리포트는 채팅 후에만 생성 가능**
   - 최소 2개 이상의 메시지가 있어야 합니다
   - 1차 적합도와 채팅 분석을 종합합니다

---

## 에러 처리

- **세션을 찾을 수 없음 (404)**: 세션 ID가 잘못되었거나 삭제됨
- **채팅 내역 부족 (400)**: 최종 리포트 생성 시 메시지가 2개 미만
- **교수님 ID 없음 (400)**: `/chat` API 호출 시 `professor_id` 필수

