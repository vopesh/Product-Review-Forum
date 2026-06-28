import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
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
    __table_args__ = (
        CheckConstraint("like_count >= 0", name="ck_comments_like_count_non_negative"),
        CheckConstraint(
            "dislike_count >= 0", name="ck_comments_dislike_count_non_negative"
        ),
    )

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    dislike_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CommentReactionVote(Base):
    __tablename__ = "comment_reactions"
    __table_args__ = (
        CheckConstraint(
            "reaction IN ('like', 'dislike')",
            name="ck_comment_reactions_reaction_value",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR anonymous_id IS NOT NULL",
            name="ck_comment_reactions_actor_required",
        ),
        UniqueConstraint(
            "comment_id", "user_id", name="uq_comment_reactions_comment_user"
        ),
        UniqueConstraint(
            "comment_id", "anonymous_id", name="uq_comment_reactions_comment_anonymous"
        ),
    )

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    comment_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    anonymous_id = Column(String, index=True, nullable=True)
    reaction = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
