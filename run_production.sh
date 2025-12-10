#!/bin/bash

# Advisor AI API 프로덕션 서버 실행 스크립트 (Gunicorn 사용)

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# Gunicorn으로 실행 (더 안정적)
gunicorn api:app \
    --workers ${API_WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${API_PORT:-8000} \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

