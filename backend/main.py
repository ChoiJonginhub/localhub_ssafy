from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

from database import Post, get_db
from routers import chat

app = FastAPI(title="Localhub Anonymous Community API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
def create_post(category: str, payload: PostCreate, db=Depends(get_db)):
    post = Post(
        category=category,
        title=payload.title,
        content=payload.content,
        password=payload.password,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


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
def delete_post(category: str, post_id: int, payload: PostDelete, db=Depends(get_db)):
    post = db.query(Post).filter(Post.category == category, Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="Password does not match")

    db.delete(post)
    db.commit()
    return None