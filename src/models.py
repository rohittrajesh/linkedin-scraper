# src/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db import Base

class Profile(Base):
    __tablename__ = "profiles"

    id         = Column(Integer, primary_key=True, index=True)
    url        = Column(String, unique=True, index=True, nullable=False)
    name       = Column(String, nullable=True)
    headline   = Column(String, nullable=True)
    location   = Column(String, nullable=True)
    email      = Column(String, nullable=True)
    phone      = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    posts = relationship(
        "Post",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

class Post(Base):
    __tablename__ = "posts"

    id         = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    post_url   = Column(String, nullable=True)
    content    = Column(Text, nullable=True)
    posted_at  = Column(DateTime, nullable=True)

    profile = relationship("Profile", back_populates="posts")