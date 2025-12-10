#!/bin/bash

# Advisor AI API 서버 실행 스크립트

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# 서버 실행
uvicorn api:app \
    --host 0.0.0.0 \
    --port ${API_PORT:-8000} \
    --workers ${API_WORKERS:-4} \
    --log-level info \
    --access-log \
    --no-reload

