from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func

from database import Comment, Meetup, Post, get_db
from routers import chat

import json
from pathlib import Path

app = FastAPI(title="Localhub Anonymous Community API")

COMMUNITY_OPTIONS = {
    "regions": [
        "강남구",
        "강동구",
        "강북구",
        "강서구",
        "관악구",
        "광진구",
        "구로구",
        "금천구",
        "노원구",
        "도봉구",
        "동대문구",
        "동작구",
        "마포구",
        "서대문구",
        "서초구",
        "성동구",
        "성북구",
        "송파구",
        "양천구",
        "영등포구",
        "용산구",
        "은평구",
        "종로구",
        "중구",
        "중랑구",
    ],
    "categories": ["맛집", "카페", "관광", "숙소", "교통", "행사", "쇼핑", "사진명소"],
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://44afy.netlify.app",
        "http://44afy.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    password: str = Field(min_length=1, max_length=100)
    region: str = Field(default="기타")
    category: str = Field(default="기타")
    visitor_count: int = Field(default=0, ge=0)


class PostUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    password: str = Field(min_length=1, max_length=100)
    region: str = Field(default="기타")
    category: str = Field(default="기타")
    visitor_count: int = Field(default=0, ge=0)


class PostDelete(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    board_category: str
    category: str
    title: str
    content: str
    region: str
    like_count: int
    view_count: int
    visitor_count: int
    comments: List[CommentResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class MeetupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    host_nickname: str = Field(min_length=1, max_length=100)
    recruitment_count: int = Field(default=1, ge=1)
    recruitment_period: str = Field(min_length=1, max_length=50)
    activity_content: str = Field(min_length=1, max_length=2000)
    location: str = Field(min_length=1, max_length=200)
    latitude: float = Field(default=37.5665)
    longitude: float = Field(default=126.9780)


class MeetupJoin(BaseModel):
    participant_nickname: str = Field(min_length=1, max_length=100)


class MeetupResponse(BaseModel):
    id: int
    title: str
    host_nickname: str
    recruitment_count: int
    recruitment_period: str
    activity_content: str
    location: str
    latitude: float
    longitude: float
    current_participants: int
    participants: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.active_clients = set()
        self.client_connection_counts = {}
        self.connection_clients = {}

    async def connect(self, websocket: WebSocket, client_id: str | None = None) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        client_key = client_id or "anonymous"
        self.connection_clients[websocket] = client_key
        if client_key not in self.client_connection_counts:
            self.active_clients.add(client_key)
        self.client_connection_counts[client_key] = self.client_connection_counts.get(client_key, 0) + 1
        await self.broadcast_presence()

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        client_key = self.connection_clients.pop(websocket, None)
        if client_key is not None:
            self.client_connection_counts[client_key] = self.client_connection_counts.get(client_key, 0) - 1
            if self.client_connection_counts[client_key] <= 0:
                self.client_connection_counts.pop(client_key, None)
                self.active_clients.discard(client_key)
        self.broadcast_presence_sync()

    async def broadcast_presence(self) -> None:
        payload = {"type": "presence", "count": len(self.active_clients), "connected": True}
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                self.disconnect(connection)

    def broadcast_presence_sync(self) -> None:
        payload = {"type": "presence", "count": len(self.active_clients), "connected": True}
        for connection in list(self.active_connections):
            try:
                import asyncio

                asyncio.create_task(connection.send_json(payload))
            except Exception:
                pass

    async def broadcast_post(self, post: PostResponse) -> None:
        post_payload = post.model_dump() if hasattr(post, "model_dump") else post.dict()
        if isinstance(post_payload.get("created_at"), datetime):
            post_payload["created_at"] = post_payload["created_at"].isoformat()
        if isinstance(post_payload.get("updated_at"), datetime):
            post_payload["updated_at"] = post_payload["updated_at"].isoformat()
        payload = {"type": "new_post", "post": post_payload}
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
def root():
    return {"message": "Anonymous community API is running"}


def serialize_post(post: Post) -> dict:
    return {
        "id": post.id,
        "board_category": post.board_category,
        "category": post.category,
        "title": post.title,
        "content": post.content,
        "region": post.region,
        "like_count": post.like_count,
        "view_count": post.view_count,
        "visitor_count": post.visitor_count,
        "comments": [
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at,
            }
            for comment in post.comments
        ],
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


def serialize_meetup(meetup: Meetup) -> dict:
    participants = json.loads(meetup.participants or "[]")
    return {
        "id": meetup.id,
        "title": meetup.title,
        "host_nickname": meetup.host_nickname,
        "recruitment_count": meetup.recruitment_count,
        "recruitment_period": meetup.recruitment_period,
        "activity_content": meetup.activity_content,
        "location": meetup.location,
        "latitude": float(meetup.latitude),
        "longitude": float(meetup.longitude),
        "current_participants": meetup.current_participants,
        "participants": participants,
        "created_at": meetup.created_at,
        "updated_at": meetup.updated_at,
    }


@app.get("/api/community/options")
def get_community_options():
    return COMMUNITY_OPTIONS


@app.get("/api/boards/{category}/posts", response_model=list[PostResponse])
def list_posts(category: str, db=Depends(get_db)):
    posts = (
        db.query(Post)
        .filter(Post.board_category == category)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [serialize_post(post) for post in posts]


@app.post("/api/boards/{category}/posts", response_model=PostResponse, status_code=201)
async def create_post(category: str, payload: PostCreate, db=Depends(get_db)):
    post = Post(
        board_category=category,
        region=payload.region,
        category=payload.category,
        title=payload.title,
        content=payload.content,
        password=payload.password,
        visitor_count=payload.visitor_count,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    response = serialize_post(post)
    await manager.broadcast_post(PostResponse(**response))
    return response


@app.get("/api/boards/{category}/posts/{post_id}", response_model=PostResponse)
def get_post(category: str, post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_post(post)


@app.put("/api/boards/{category}/posts/{post_id}", response_model=PostResponse)
def update_post(category: str, post_id: int, payload: PostUpdate, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="Password does not match")

    post.region = payload.region
    post.category = payload.category
    post.title = payload.title
    post.content = payload.content
    post.visitor_count = payload.visitor_count
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@app.delete("/api/boards/{category}/posts/{post_id}", status_code=204)
async def delete_post(category: str, post_id: int, payload: PostDelete, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="Password does not match")

    db.delete(post)
    db.commit()
    return None


@app.post("/api/boards/{category}/posts/{post_id}/like", response_model=PostResponse)
def like_post(category: str, post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.like_count += 1
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@app.post("/api/boards/{category}/posts/{post_id}/view", response_model=PostResponse)
def view_post(category: str, post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.view_count += 1
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@app.post("/api/boards/{category}/posts/{post_id}/comments", response_model=PostResponse, status_code=201)
def add_comment(category: str, post_id: int, payload: CommentCreate, db=Depends(get_db)):
    post = db.query(Post).filter(Post.board_category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(content=payload.content, post=post)
    db.add(comment)
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@app.post("/api/meetups", response_model=MeetupResponse, status_code=201)
def create_meetup(payload: MeetupCreate, db=Depends(get_db)):
    participants = [payload.host_nickname]
    meetup = Meetup(
        title=payload.title,
        host_nickname=payload.host_nickname,
        recruitment_count=payload.recruitment_count,
        recruitment_period=payload.recruitment_period,
        activity_content=payload.activity_content,
        location=payload.location,
        latitude=str(payload.latitude),
        longitude=str(payload.longitude),
        current_participants=1,
        participants=json.dumps(participants),
    )
    db.add(meetup)
    db.commit()
    db.refresh(meetup)
    return serialize_meetup(meetup)


@app.get("/api/meetups", response_model=list[MeetupResponse])
def list_meetups(db=Depends(get_db)):
    meetups = db.query(Meetup).order_by(Meetup.created_at.desc()).all()
    return [serialize_meetup(meetup) for meetup in meetups]


@app.post("/api/meetups/{meetup_id}/join", response_model=MeetupResponse)
def join_meetup(meetup_id: int, payload: MeetupJoin, db=Depends(get_db)):
    meetup = db.query(Meetup).filter(Meetup.id == meetup_id).first()
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    participants = json.loads(meetup.participants or "[]")
    if payload.participant_nickname in participants:
        raise HTTPException(status_code=400, detail="Already joined")
    if meetup.current_participants >= meetup.recruitment_count:
        raise HTTPException(status_code=400, detail="Recruitment full")

    participants.append(payload.participant_nickname)
    meetup.participants = json.dumps(participants)
    meetup.current_participants = len(participants)
    db.commit()
    db.refresh(meetup)
    return serialize_meetup(meetup)


@app.get("/api/statistics/regions")
def get_region_statistics(db=Depends(get_db)):
    region_rows = (
        db.query(Post.region.label("region"), func.count(Post.id).label("post_count"))
        .group_by(Post.region)
        .all()
    )
    category_rows = (
        db.query(Post.category.label("category"), func.count(Post.id).label("post_count"))
        .filter(Post.category != "seoul")
        .group_by(Post.category)
        .all()
    )

    regions = [{"region": row.region, "post_count": row.post_count} for row in region_rows]
    categories = [{"category": row.category, "post_count": row.post_count} for row in category_rows]
    regions.sort(key=lambda item: item["post_count"], reverse=True)
    categories.sort(key=lambda item: item["post_count"], reverse=True)

    views_rows = (
        db.query(Post.region.label("region"), func.sum(Post.view_count).label("total_views"))
        .group_by(Post.region)
        .all()
    )
    likes_rows = (
        db.query(Post.region.label("region"), func.sum(Post.like_count).label("total_likes"))
        .group_by(Post.region)
        .all()
    )

    daily_views_rows = (
        db.query(
            func.strftime('%Y-%m-%d', Post.created_at).label('date'),
            Post.category.label('category'),
            func.sum(Post.view_count).label('total_views'),
        )
        .filter(Post.category != 'seoul')
        .group_by(func.strftime('%Y-%m-%d', Post.created_at), Post.category)
        .order_by('date', 'category')
        .all()
    )

    weekly_posts_rows = (
        db.query(
            func.strftime('%Y-%m-%d', Post.created_at).label('date'),
            func.count(Post.id).label('post_count'),
        )
        .filter(Post.created_at >= datetime.utcnow() - timedelta(days=6))
        .group_by(func.strftime('%Y-%m-%d', Post.created_at))
        .order_by('date')
        .all()
    )

    hourly_posts_rows = (
        db.query(
            func.strftime('%H', Post.created_at).label('hour'),
            func.count(Post.id).label('post_count'),
        )
        .group_by(func.strftime('%H', Post.created_at))
        .order_by('hour')
        .all()
    )

    recent_posts = (
        db.query(Post)
        .order_by(Post.view_count.desc(), Post.like_count.desc(), Post.created_at.desc())
        .limit(5)
        .all()
    )

    top_posts = []
    for post in recent_posts:
        top_posts.append({
            "id": post.id,
            "title": post.title,
            "category": post.category,
            "region": post.region,
            "writer": "익명",
            "views": post.view_count,
            "likes": post.like_count,
        })

    return {
        "total_posts": db.query(Post).count(),
        "region_count": len(regions),
        "regions": regions,
        "popular_regions": regions[:5],
        "categories": categories,
        "popular_categories": categories[:5],
        "views": [
            {"region": row.region, "total_views": int(row.total_views or 0)} for row in views_rows
        ],
        "likes": [
            {"region": row.region, "total_likes": int(row.total_likes or 0)} for row in likes_rows
        ],
        "category_daily_views": [
            {"date": row.date, "category": row.category, "total_views": int(row.total_views or 0)} for row in daily_views_rows
        ],
        "weekly_posts": [
            {"date": row.date, "post_count": int(row.post_count or 0)} for row in weekly_posts_rows
        ],
        "hourly_posts": [
            {"hour": row.hour, "visitor_count": int(row.post_count or 0)} for row in hourly_posts_rows
        ],
        "top_posts": top_posts,
    }


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    client_id = websocket.query_params.get("client_id")
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/tourist")
def get_tourist_places():
    file_path = Path(__file__).parent / "data" / "서울_관광지.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Tourist data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/leports")
def get_leports_places():
    file_path = Path(__file__).parent / "data" / "서울_레포츠.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Leports data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/culture")
def get_culture_places():
    file_path = Path(__file__).parent / "data" / "서울_문화시설.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="culture data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/shop")
def get_shop_places():
    file_path = Path(__file__).parent / "data" / "서울_쇼핑.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="shop data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/lodge")
def get_lodge_places():
    file_path = Path(__file__).parent / "data" / "서울_숙박.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="lodge data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/course")
def get_course_places():
    file_path = Path(__file__).parent / "data" / "서울_여행코스.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="course data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

@app.get("/api/festival")
def get_festival_places():
    file_path = Path(__file__).parent / "data" / "서울_축제공연행사.json"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="festival data file not found"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data.get("items", []):
        if item.get("mapx") and item.get("mapy"):
            result.append({
                "id": item["contentid"],
                "title": item["title"],
                "address": item["addr1"],
                "lat": float(item["mapy"]),
                "lng": float(item["mapx"]),
                "image": item.get("firstimage", "")
            })

    return result

