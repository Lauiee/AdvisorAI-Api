import os
from openai import OpenAI
from pinecone import Pinecone
from database import SessionLocal, Professor
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
# 2. 모델 설정
# -----------------------------
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# -----------------------------
# 3. 텍스트 임베딩 함수
# -----------------------------
def embed_text(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


# -----------------------------
# 3. Pinecone에서 유사한 벡터 검색
# -----------------------------
def search_similar_chunks(query: str, top_k: int = 3, professor_id: str = None):
    # 질문을 임베딩
    query_vector = embed_text(query)
    
    # Pinecone에서 유사한 벡터 검색
    # professor_id가 지정되면 해당 교수님의 데이터만 검색
    query_params = {
        "vector": query_vector,
        "top_k": top_k,
        "include_metadata": True
    }
    
    # professor_id 필터 추가
    if professor_id:
        query_params["filter"] = {"professor_id": {"$eq": professor_id}}
    
    results = index.query(**query_params)
    
    return results.matches


# -----------------------------
# 4. 컨텍스트 구성
# -----------------------------
def format_context(matches):
    context_parts = []
    
    for match in matches:
        metadata = match.metadata
        score = match.score
        
        if metadata.get("type") == "qa":
            # Q&A 타입인 경우
            question = metadata.get("question", "")
            answer = metadata.get("answer", "")
            context_parts.append(f"질문: {question}\n답변: {answer}")
        else:
            # 프로필 타입인 경우
            title = metadata.get("title", "")
            text = metadata.get("text", "")
            context_parts.append(f"[{title}]\n{text}")
    
    return "\n\n".join(context_parts)


# -----------------------------
# 5. 교수님 이름 조회 함수
# -----------------------------
def get_professor_name(professor_id: str) -> str:
    """데이터베이스에서 professor_id로 교수님 이름 조회"""
    if not professor_id:
        return "교수님"
    
    db = SessionLocal()
    try:
        professor = db.query(Professor).filter(Professor.professor_id == professor_id).first()
        if professor:
            return professor.name
        return "교수님"
    except Exception:
        return "교수님"
    finally:
        db.close()


# -----------------------------
# 6. RAG 기반 답변 생성
# -----------------------------
def generate_answer(user_question: str, top_k: int = 3, professor_id: str = None):
    # 1. 교수님 이름 조회
    professor_name = get_professor_name(professor_id) if professor_id else None
    
    # 2. 자기소개 관련 질문인지 확인
    is_intro_question = any(keyword in user_question for keyword in ["자기소개", "소개", "프로필", "경력", "학력", "어떤 분"])
    
    # 3. 유사한 벡터 검색 (professor_id로 필터링)
    # 자기소개 관련 질문은 더 많은 결과를 검색하여 프로필 정보도 포함
    search_k = max(top_k * 3, 10) if is_intro_question else top_k
    matches = search_similar_chunks(user_question, top_k=search_k, professor_id=professor_id)
    
    if not matches:
        return "관련 정보를 찾을 수 없습니다.", []
    
    # 4. 컨텍스트 구성 (프로필 정보를 우선적으로 포함)
    # 프로필 정보와 Q&A를 분리
    profile_matches = [m for m in matches if m.metadata.get("type") == "profile"]
    qa_matches = [m for m in matches if m.metadata.get("type") == "qa"]
    
    # 자기소개 질문인 경우 프로필 정보를 강제로 포함
    if is_intro_question and professor_id:
        # 프로필 정보를 별도로 검색하여 추가
        profile_query = f"{professor_name if professor_name else '교수님'} 소개 경력 학력"
        profile_search_results = search_similar_chunks(profile_query, top_k=5, professor_id=professor_id)
        additional_profiles = [m for m in profile_search_results if m.metadata.get("type") == "profile"]
        # 중복 제거
        existing_chunk_ids = {m.metadata.get("chunk_id") for m in profile_matches}
        for m in additional_profiles:
            if m.metadata.get("chunk_id") not in existing_chunk_ids:
                profile_matches.append(m)
    
    # 자기소개 질문인 경우 프로필 정보를 우선적으로 포함
    if is_intro_question:
        # 프로필 정보를 최대한 포함 (교수 소개, 기본 정보, 경력, 학력 등)
        sorted_matches = profile_matches[:5] + qa_matches[:2]
    else:
        # 일반 질문은 Q&A 우선
        sorted_matches = profile_matches[:2] + qa_matches[:top_k]
    
    context = format_context(sorted_matches)
    
    # 4. 프롬프트 구성
    if professor_name:
        system_prompt = f"""당신은 {professor_name} 교수님입니다. 학생들의 질문에 직접적으로 답변하는 역할을 합니다.
제공된 교수님의 실제 답변과 정보를 바탕으로, 교수님의 말투와 스타일로 자연스럽게 답변해주세요.
답변은 1인칭(저, 제가, 저는 등)으로 작성하고, 교수님이 직접 말씀하시는 것처럼 친절하고 명확하게 작성해주세요."""
    else:
        system_prompt = """당신은 교수님입니다. 학생들의 질문에 직접적으로 답변하는 역할을 합니다.
제공된 교수님의 실제 답변과 정보를 바탕으로, 교수님의 말투와 스타일로 자연스럽게 답변해주세요.
답변은 1인칭(저, 제가, 저는 등)으로 작성하고, 교수님이 직접 말씀하시는 것처럼 친절하고 명확하게 작성해주세요."""

    user_prompt = f"""다음은 교수님의 실제 답변과 정보입니다:

{context}

학생 질문: {user_question}

위 정보를 바탕으로 학생의 질문에 교수님의 입장에서 직접 답변해주세요. 
- 1인칭(저, 제가, 저는)으로 답변하세요
- "교수님은 ~하십니다" 같은 3인칭 표현은 사용하지 마세요
- 제공된 정보에 없는 내용은 추측하지 말고, 제공된 정보만을 사용해서 답변해주세요
- 교수님의 실제 답변 스타일을 참고하여 자연스럽게 답변해주세요"""

    # 4. LLM으로 답변 생성
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    )
    
    answer = response.choices[0].message.content
    
    # 5. 참고한 정보도 함께 반환
    references = []
    for match in matches:
        metadata = match.metadata
        if metadata.get("type") == "qa":
            references.append(f"- {metadata.get('question', '')}")
        else:
            references.append(f"- {metadata.get('title', '')}")
    
    return answer, references


# -----------------------------
# 6. 대화 루프
# -----------------------------
def chat_loop():
    print("=" * 60)
    print("교수님 연구 스타일 및 지도 방식 안내 AI")
    print("=" * 60)
    print("질문을 입력하세요. '종료' 또는 'exit'를 입력하면 대화를 종료합니다.\n")
    
    while True:
        user_input = input("질문: ").strip()
        
        if user_input.lower() in ["종료", "exit", "quit", "q"]:
            print("\n대화를 종료합니다. 감사합니다!")
            break
        
        if not user_input:
            continue
        
        print("\n답변 생성 중...\n")
        
        try:
            answer, references = generate_answer(user_input)
            
            print("답변:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
            
            if references:
                print("\n참고한 정보:")
                for ref in references:
                    print(ref)
            
            print("\n")
            
        except Exception as e:
            print(f"오류가 발생했습니다: {e}\n")


# -----------------------------
# 7. 테스트 함수
# -----------------------------
def test_single_question(question: str):
    """단일 질문 테스트용 함수"""
    print(f"질문: {question}\n")
    print("답변 생성 중...\n")
    
    try:
        answer, references = generate_answer(question)
        
        print("답변:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
        
        if references:
            print("\n참고한 정보:")
            for ref in references:
                print(ref)
        
        print("\n")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}\n")


# -----------------------------
# 8. 실행
# -----------------------------
if __name__ == "__main__":
    import sys
    
    # 명령줄 인자가 있으면 테스트 모드
    if len(sys.argv) > 1:
        test_question = " ".join(sys.argv[1:])
        test_single_question(test_question)
    else:
        chat_loop()

