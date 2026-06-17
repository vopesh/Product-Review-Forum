import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text
from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_id = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    purchase_source = Column(String, nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_country = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    user_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
