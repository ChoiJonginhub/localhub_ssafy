from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import Post, get_db
from routers import chat

app = FastAPI(title="Localhub Anonymous Community API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    password: str = Field(min_length=1, max_length=100)


class PostUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    password: str = Field(min_length=1, max_length=100)


class PostDelete(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostResponse(BaseModel):
    id: int
    category: str
    title: str
    content: str
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


@app.get("/api/boards/{category}/posts", response_model=list[PostResponse])
def list_posts(category: str, db=Depends(get_db)):
    posts = (
        db.query(Post)
        .filter(Post.category == category)
        .order_by(Post.created_at.desc())
        .all()
    )
    return posts


@app.post("/api/boards/{category}/posts", response_model=PostResponse, status_code=201)
async def create_post(category: str, payload: PostCreate, db=Depends(get_db)):
    post = Post(
        category=category,
        title=payload.title,
        content=payload.content,
        password=payload.password,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    response = PostResponse(
        id=post.id,
        category=post.category,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )
    await manager.broadcast_post(response)
    return response


@app.get("/api/boards/{category}/posts/{post_id}", response_model=PostResponse)
def get_post(category: str, post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.put("/api/boards/{category}/posts/{post_id}", response_model=PostResponse)
def update_post(category: str, post_id: int, payload: PostUpdate, db=Depends(get_db)):
    post = db.query(Post).filter(Post.category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="Password does not match")

    post.title = payload.title
    post.content = payload.content
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post


@app.delete("/api/boards/{category}/posts/{post_id}", status_code=204)
async def delete_post(category: str, post_id: int, payload: PostDelete, db=Depends(get_db)):
    post = db.query(Post).filter(Post.category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="Password does not match")

    db.delete(post)
    db.commit()
    return None


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    client_id = websocket.query_params.get("client_id")
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)