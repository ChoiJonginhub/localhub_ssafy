import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency for local testing
    Anthropic = None

from database import ChatMessage, Post, get_db
from services import tour_data

router = APIRouter(prefix="/api/chat", tags=["chat"])

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 계정에서 사용 가능한 모델로 바꿔도 됨 (예: "gpt-4o", "gpt-4o-mini")
MODEL_NAME = "gpt-5.6"

SYSTEM_PROMPT = (
    "당신은 서울 지역 정보 안내 챗봇입니다. "
    "관광지, 레포츠, 문화시설, 쇼핑, 숙박, 여행코스, 축제/공연/행사와 관련된 질문이면 "
    "반드시 search_local_info 도구로 실제 데이터를 조회한 뒤 그 결과를 근거로 답변하세요. "
    "커뮤니티 게시글을 찾아달라는 질문이면 search_community_posts 도구를 사용하세요. "
    "도구 조회 결과에 없는 내용은 추측해서 답하지 말고, 없다고 솔직히 답하세요. "
    "답변은 간결한 한국어 존댓말로 작성하세요."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_local_info",
            "description": "서울 지역의 관광지/레포츠/문화시설/쇼핑/숙박/여행코스/축제공연행사 정보를 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "관광지",
                            "레포츠",
                            "문화시설",
                            "쇼핑",
                            "숙박",
                            "여행코스",
                            "축제공연행사",
                        ],
                        "description": "검색할 카테고리. 지정하지 않으면 전체 카테고리에서 검색.",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "제목에 포함될 검색어 (예: '한강', '박물관')",
                    },
                    "district": {
                        "type": "string",
                        "description": "구/동 이름 (예: '강남구', '홍대')",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_community_posts",
            "description": "커뮤니티 게시판의 게시글을 제목/내용 키워드로 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "검색할 키워드"},
                    "category": {"type": "string", "description": "게시판 카테고리 (선택)"},
                },
                "required": ["keyword"],
            },
        },
    },
]


def _run_tool(name: str, arguments: dict, db: Session) -> list[dict]:
    if name == "search_local_info":
        return tour_data.search(
            category=arguments.get("category"),
            keyword=arguments.get("keyword"),
            district=arguments.get("district"),
        )

    if name == "search_community_posts":
        q = db.query(Post)
        if arguments.get("category"):
            q = q.filter(Post.category == arguments["category"])
        keyword = arguments.get("keyword", "")
        if keyword:
            q = q.filter(Post.title.contains(keyword) | Post.content.contains(keyword))
        posts = q.order_by(Post.created_at.desc()).limit(10).all()
        return [{"id": p.id, "title": p.title, "category": p.category} for p in posts]

    return []


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


def _converse(messages: list, db: Session, max_turns: int = 4) -> str:
    
    """도구 호출 루프: 모델이 tool_calls를 반환하면 실행하고 결과를 다시 넘겨 최종 답변을 받는다."""

    for _ in range(max_turns):
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            result = _run_tool(tool_call.function.name, args, db)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "죄송해요, 지금은 답변을 생성하지 못했어요. 다시 질문해 주시겠어요?"


@router.post("/send", response_model=ChatMessageResponse)
def send_message(payload: ChatRequest, db: Session = Depends(get_db)):
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == payload.session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    user_msg = ChatMessage(session_id=payload.session_id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    messages = [{"role": h.role, "content": h.content} for h in history]
    messages.append({"role": "user", "content": payload.message})

    try:
        reply_text = _converse(messages, db)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Chat API error: {e}")

    assistant_msg = ChatMessage(session_id=payload.session_id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg


@router.get("/history/{session_id}", response_model=list[ChatMessageResponse])
def get_history(session_id: str, db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )