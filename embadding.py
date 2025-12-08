import json
import os
from tqdm import tqdm
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# -----------------------------
# 1. API Keys 설정
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-advise")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# -----------------------------
# 2. JSON 파일 읽기
# -----------------------------
# 예시: professor_data.json
# [
#   {
#     "professor_id": "prof_001",
#     "chunk_id": "prof_001_Q1",
#     "content": "Q1: ... A1: ..."
#   },
#   ...
# ]
with open("professor_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# -----------------------------
# 3. 모델 설정
# -----------------------------
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# -----------------------------
# 4. 텍스트 임베딩 함수
# -----------------------------
def embed_text(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,  # 1536 차원 (인덱스와 일치)
        input=text
    )
    return response.data[0].embedding


# -----------------------------
# 4. Pinecone 업서트
# -----------------------------
def upsert_chunks(data):
    vectors = []

    for item in tqdm(data):
        # Q&A 타입인 경우 question과 answer를 함께 사용
        if item.get("type") == "qa" and "question" in item and "answer" in item:
            text = f"질문: {item['question']}\n답변: {item['answer']}"
        else:
            text = item["content"]
        
        vector = embed_text(text)

        metadata = {
            "professor_id": item["professor_id"],
            "chunk_id": item["chunk_id"],
            "type": item.get("type", ""),
            "text": text
        }
        
        # Q&A인 경우 question, answer, indicator도 메타데이터에 추가
        if item.get("type") == "qa":
            if "question" in item:
                metadata["question"] = item["question"]
            if "answer" in item:
                metadata["answer"] = item["answer"]
            if "indicator" in item:
                metadata["indicator"] = item["indicator"]
        elif "title" in item:
            metadata["title"] = item["title"]

        vectors.append({
            "id": item["chunk_id"],                   # 고유 ID
            "values": vector,                         # 임베딩 벡터
            "metadata": metadata
        })

    index.upsert(vectors=vectors)
    print(f"총 {len(vectors)}개 벡터가 업서트되었습니다.")


# -----------------------------
# 5. 실행
# -----------------------------
if __name__ == "__main__":
    upsert_chunks(data)
