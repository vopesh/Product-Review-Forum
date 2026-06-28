from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from datetime import date, datetime
from typing import Literal, Optional, List

class PostCreate(BaseModel):
    caption: str = Field(min_length=1, max_length=500, description="The description for the photo or video")
    product_name: str = Field(min_length=1, max_length=120)
    product_category: str = Field(min_length=1, max_length=80)
    purchase_source: str = Field(min_length=1, max_length=120)
    purchase_date: date
    purchase_country: str = Field(min_length=1, max_length=80)
    rating: int = Field(ge=1, le=5)

    @field_validator("caption", "product_name", "product_category", "purchase_source", "purchase_country")
    @classmethod
    def require_non_blank_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("This field is required")
        return text

class BulkDeleteRequest(BaseModel):
    post_ids: List[str]

class DeleteResponse(BaseModel):
    status: str
    message: str

class BulkDeleteResponse(BaseModel):
    status: str
    deleted_count: int


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def require_non_blank_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Comment is required")
        return text


class CommentReaction(BaseModel):
    reaction: Literal["like", "dislike"]


class CommentRead(BaseModel):
    id: str
    post_id: str
    user_id: Optional[str] = None
    content: str
    author_name: str
    can_edit_until: Optional[datetime] = None
    like_count: int = Field(default=0, ge=0)
    dislike_count: int = Field(default=0, ge=0)
    user_reaction: Optional[Literal["like", "dislike"]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PostRead(BaseModel):
    id: str
    user_id: Optional[str] = None
    caption: Optional[str] = None
    url: str
    file_type: str
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    purchase_source: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_country: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime

    @computed_field
    @property
    def thumbnail_url(self) -> str:
        """Returns a 200x200 cropped thumbnail URL using ImageKit transformations"""
        if self.file_type == "photo":
            return f"{self.url}?tr=w-200,h-200,fo-auto"
        elif self.file_type == "video":
            return self.url
        return self.url

    # This allows Pydantic to work with SQLAlchemy models (ORMs)
    model_config = ConfigDict(from_attributes=True)
