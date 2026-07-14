import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency for local testing
    Anthropic = None

from database import ChatMessage, Post, get_db
from services import tour_data

router = APIRouter(prefix="/api/chat", tags=["chat"])

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic is not None else None

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
        "name": "search_local_info",
        "description": "서울 지역의 관광지/레포츠/문화시설/쇼핑/숙박/여행코스/축제공연행사 정보를 검색합니다.",
        "input_schema": {
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
    {
        "name": "search_community_posts",
        "description": "커뮤니티 게시판의 게시글을 제목/내용 키워드로 검색합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "검색할 키워드"},
                "category": {"type": "string", "description": "게시판 카테고리 (선택)"},
            },
            "required": ["keyword"],
        },
    },
]


def _run_tool(name: str, tool_input: dict, db: Session) -> list[dict]:
    if name == "search_local_info":
        return tour_data.search(
            category=tool_input.get("category"),
            keyword=tool_input.get("keyword"),
            district=tool_input.get("district"),
        )

    if name == "search_community_posts":
        q = db.query(Post)
        if tool_input.get("category"):
            q = q.filter(Post.category == tool_input["category"])
        keyword = tool_input.get("keyword", "")
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
    """도구 호출 루프: Claude가 tool_use를 반환하면 실행하고 결과를 다시 넘겨 최종 답변을 받는다."""
    if client is None:
        return "현재 AI 서비스 키가 설정되어 있지 않아 답변을 생성할 수 없습니다."

    for _ in range(max_turns):
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _run_tool(block.name, block.input, db)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

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