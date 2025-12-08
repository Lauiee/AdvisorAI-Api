"""
SMTP를 사용한 이메일 전송 기능
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from email.header import Header

# python-dotenv 지원 (선택사항)
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경 변수 로드
except ImportError:
    # dotenv가 설치되지 않은 경우 무시
    pass

# SMTP 설정 (환경 변수에서 가져오기)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Advisor.AI")


def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> dict:
    """
    SMTP를 사용하여 이메일 전송
    
    Args:
        to_email: 수신자 이메일 주소
        subject: 이메일 제목
        body: 이메일 본문 (텍스트)
        from_email: 발신자 이메일 (기본값: SMTP_FROM_EMAIL)
        from_name: 발신자 이름 (기본값: SMTP_FROM_NAME)
    
    Returns:
        {"success": bool, "message": str}
    """
    # 환경 변수 확인
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP 설정이 완료되지 않았습니다. SMTP_USERNAME과 SMTP_PASSWORD 환경 변수를 설정해주세요."
        }
    
    if not to_email:
        return {
            "success": False,
            "message": "수신자 이메일 주소가 필요합니다."
        }
    
    from_email = from_email or SMTP_FROM_EMAIL
    from_name = from_name or SMTP_FROM_NAME
    
    try:
        # 이메일 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 본문 추가 (텍스트 형식)
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # SMTP 서버 연결 및 전송
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # TLS 암호화
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return {
            "success": True,
            "message": f"이메일이 성공적으로 전송되었습니다. (수신자: {to_email})"
        }
    
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "SMTP 인증 실패. 사용자 이름과 비밀번호를 확인해주세요."
        }
    except smtplib.SMTPRecipientsRefused:
        return {
            "success": False,
            "message": f"수신자 이메일 주소가 유효하지 않습니다: {to_email}"
        }
    except smtplib.SMTPServerDisconnected:
        return {
            "success": False,
            "message": "SMTP 서버 연결이 끊어졌습니다. 서버 설정을 확인해주세요."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"이메일 전송 중 오류가 발생했습니다: {str(e)}"
        }

