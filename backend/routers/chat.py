import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
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

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

router = APIRouter(prefix="/api/chat", tags=["chat"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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


def _get_fallback_reply(message: str) -> str:
    text = message.lower()
    if any(keyword in text for keyword in ["숙박", "호텔", "stay", "room"]):
        return "서울에서 숙소를 찾으신다면 강남·홍대·명동 주변이 접근성이 좋습니다. 예산과 원하는 분위기(비즈니스, 가족, 감성)까지 알려주시면 더 구체적으로 추천해드릴게요."
    if any(keyword in text for keyword in ["관광", "명소", "추천", "가볼만한"]):
        return "서울에서는 경복궁, 남산, 한강공원, 홍대, 성수 같은 곳이 많이 찾으시더라구요. 원하는 지역이나 취향(조용한 곳, 야경, 맛집 위주)을 알려주시면 맞춤형으로 추천해드릴게요."
    if any(keyword in text for keyword in ["축제", "행사", "공연"]):
        return "서울의 축제와 공연 정보는 계절별로 자주 바뀝니다. 원하시는 월이나 구를 알려주시면 그에 맞는 행사 정보를 더 정확히 찾아드릴게요."
    if any(keyword in text for keyword in ["맛집", "음식", "식당"]):
        return "서울은 동네별 맛집 분위기가 정말 다양합니다. 강남, 홍대, 명동, 성수처럼 원하는 동네를 알려주시면 더 잘 맞는 추천을 해드릴게요."
    return "서울 지역 정보나 커뮤니티 게시글에 대해 궁금하시면 구 이름, 장소, 관심사(숙박/관광/축제/맛집)를 함께 말해 주세요. 바로 더 구체적으로 안내해드릴게요."


def _converse(messages: list, db: Session, max_turns: int = 4) -> str:
    """도구 호출 루프: 모델이 tool_calls를 반환하면 실행하고 결과를 다시 넘겨 최종 답변을 받는다."""

    if not client:
        return "현재 OpenAI API 키가 설정되지 않아 챗봇을 바로 호출할 수 없습니다. 백엔드 .env의 OPENAI_API_KEY를 확인해 주세요."

    for _ in range(max_turns):
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=api_messages,
                tools=TOOLS,
            )
        except Exception as exc:
            latest_user_message = messages[-1]["content"] if messages else ""
            return _get_fallback_reply(latest_user_message) + f"\n\n(현재 OpenAI 호출은 제한되어 있어 로컬 안내로 응답 중입니다: {exc})"

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
        reply_text = f"챗봇 처리 중 오류가 발생했습니다. ({e})"

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