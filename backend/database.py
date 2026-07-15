from datetime import datetime
from typing import Generator

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./community.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    board_category = Column(String(50), nullable=False, index=True, default="seoul")
    region = Column(String(100), nullable=False, default="기타")
    category = Column(String(50), nullable=False, default="기타")
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)
    like_count = Column(Integer, nullable=False, default=0)
    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    post = relationship("Post", back_populates="comments")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(String(4000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def ensure_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "posts" not in tables or "comments" not in tables:
        Base.metadata.create_all(bind=engine)
        return

    posts_columns = {column["name"] for column in inspector.get_columns("posts")}

    with engine.begin() as connection:
        if "board_category" not in posts_columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN board_category VARCHAR(50) DEFAULT 'seoul'"))
        if "region" not in posts_columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN region VARCHAR(100) DEFAULT '기타'"))
        if "category" not in posts_columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN category VARCHAR(50) DEFAULT '기타'"))
        if "like_count" not in posts_columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN like_count INTEGER DEFAULT 0"))
        if "view_count" not in posts_columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN view_count INTEGER DEFAULT 0"))

    if "comments" not in tables:
        Base.metadata.create_all(bind=engine)


ensure_schema()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()