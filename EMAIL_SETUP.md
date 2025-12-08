# 이메일 전송 설정 가이드

## SMTP 환경 변수 설정

이메일 전송 기능을 사용하려면 다음 환경 변수를 설정해야 합니다.

### 필수 환경 변수

```bash
# SMTP 서버 설정
export SMTP_SERVER="smtp.gmail.com"  # Gmail의 경우
export SMTP_PORT="587"  # TLS 포트 (일반적으로 587 또는 465)
export SMTP_USERNAME="your-email@gmail.com"  # 발신자 이메일 주소
export SMTP_PASSWORD="your-app-password"  # 앱 비밀번호 (Gmail의 경우)
export SMTP_FROM_EMAIL="your-email@gmail.com"  # 발신자 이메일 (기본값: SMTP_USERNAME)
export SMTP_FROM_NAME="Advisor.AI"  # 발신자 이름 (기본값: "Advisor.AI")
```

### Gmail 설정 방법

1. **2단계 인증 활성화**
   - Google 계정 설정 → 보안 → 2단계 인증 활성화

2. **앱 비밀번호 생성**
   - Google 계정 설정 → 보안 → 2단계 인증 → 앱 비밀번호
   - "메일" 및 "기타(맞춤 이름)" 선택
   - 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 사용

3. **환경 변수 설정**
   ```bash
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USERNAME="your-email@gmail.com"
   export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"  # 앱 비밀번호 (공백 제거)
   ```

### 다른 이메일 서비스 설정

#### Outlook/Hotmail
```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@outlook.com"
export SMTP_PASSWORD="your-password"
```

#### 네이버 메일
```bash
export SMTP_SERVER="smtp.naver.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@naver.com"
export SMTP_PASSWORD="your-password"
```

#### 네이트 메일
```bash
export SMTP_SERVER="smtp.mail.nate.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@nate.com"
export SMTP_PASSWORD="your-password"
```

### 환경 변수 영구 설정 (선택사항)

#### Linux/macOS
`~/.bashrc` 또는 `~/.zshrc`에 추가:
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM_EMAIL="your-email@gmail.com"
export SMTP_FROM_NAME="Advisor.AI"
```

#### Windows
시스템 환경 변수로 설정하거나, PowerShell에서:
```powershell
$env:SMTP_SERVER="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your-email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
```

### .env 파일 사용 (권장)

프로젝트 루트에 `.env` 파일을 생성하고 `python-dotenv`를 사용:

1. `python-dotenv` 설치:
```bash
pip install python-dotenv
```

2. 프로젝트 루트에 `.env` 파일 생성:
```bash
# .env 파일 내용
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Advisor.AI
```

**참고:** `email_sender.py`는 이미 `python-dotenv`를 자동으로 로드하도록 설정되어 있습니다. 
`python-dotenv`가 설치되어 있으면 `.env` 파일을 자동으로 읽어옵니다.

**중요:** `.env` 파일은 Git에 커밋하지 마세요! `.gitignore`에 추가되어 있는지 확인하세요.

## API 사용 방법

### 1. 이메일 초안 생성
```bash
POST /email/draft
{
  "applicant_id": 1,
  "professor_id": "prof_001",
  "session_id": 1,  # 선택사항
  "appointment_date": "2025년 12월 17일",
  "appointment_time": "오후 3시 12분",
  "consultation_method": "대면"
}
```

### 2. 이메일 전송
```bash
POST /email/send
{
  "applicant_id": 1,
  "professor_id": "prof_001",
  "email_subject": "상담 요청 드립니다",
  "email_body": "이메일 초안 내용...",
  "from_email": "optional@example.com",  # 선택사항
  "from_name": "지원자 이름"  # 선택사항
}
```

## 교수님 이메일 주소 등록

교수님의 이메일 주소는 데이터베이스의 `professors` 테이블에 저장되어야 합니다.

```python
# 예시: 교수님 이메일 업데이트
professor = db.query(Professor).filter(Professor.professor_id == "prof_001").first()
professor.email = "professor@university.edu"
db.commit()
```

## 문제 해결

### 인증 실패
- Gmail의 경우 앱 비밀번호를 사용해야 합니다
- 2단계 인증이 활성화되어 있어야 합니다
- 비밀번호에 공백이 포함되어 있지 않은지 확인하세요

### 연결 실패
- 방화벽에서 포트 587 또는 465가 차단되지 않았는지 확인
- SMTP 서버 주소가 올바른지 확인

### 수신자 오류
- 교수님의 이메일 주소가 데이터베이스에 올바르게 저장되어 있는지 확인
- 이메일 주소 형식이 올바른지 확인

