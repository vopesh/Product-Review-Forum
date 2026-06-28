import logging
from datetime import date, datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from fastapi import APIRouter, Depends, File, UploadFile, Form, BackgroundTasks, Header
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, or_, select
from app.database.db import get_async_session
from app.models.models import Comment, CommentReactionVote, Post
from app.core.exceptions import AppException
from app.core.logger import logger
from app.core.imagekit import upload_media, delete_media, bulk_delete_media
from app.core.security import get_current_user, get_optional_current_user
from app.models.models import User
from app.schemas.post_schemas import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    CommentCreate,
    CommentReaction,
    CommentRead,
    DeleteResponse,
    PostCreate,
    PostRead,
)
from typing import List, Optional

router = APIRouter()
COMMENT_EDIT_WINDOW = timedelta(minutes=15)

# Background Task Helpers
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=False  # Don't crash the background thread worker if it ultimately fails
)
def bg_delete_imagekit_file(file_id: str) -> None:
    """Helper to delete a single file from ImageKit in the background"""
    delete_media(file_id)
    logger.info(f"Background task: Successfully deleted file {file_id} from ImageKit")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=False
)
def bg_bulk_delete_imagekit_files(file_ids: List[str]) -> None:
    """Helper to bulk delete files from ImageKit in the background"""
    bulk_delete_media(file_ids)
    logger.info(f"Background task: Successfully bulk deleted {len(file_ids)} files from ImageKit")


def get_user_display_name(user: User) -> str:
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)
    return full_name or user.email


def can_change_comment(comment: Comment) -> bool:
    return datetime.now() <= comment.created_at + COMMENT_EDIT_WINDOW


def to_comment_read(comment: Comment, user: User | None, user_reaction: Optional[str] = None) -> CommentRead:
    return CommentRead(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        author_name=get_user_display_name(user) if user else "Anonymous user",
        can_edit_until=comment.created_at + COMMENT_EDIT_WINDOW if comment.user_id else None,
        like_count=comment.like_count or 0,
        dislike_count=comment.dislike_count or 0,
        user_reaction=user_reaction,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def reaction_actor_filter(
    comment_id: str,
    current_user: Optional[User],
    anonymous_id: Optional[str],
):
    if current_user:
        return (
            CommentReactionVote.comment_id == comment_id,
            CommentReactionVote.user_id == current_user.id,
        )
    if anonymous_id:
        return (
            CommentReactionVote.comment_id == comment_id,
            CommentReactionVote.anonymous_id == anonymous_id,
        )
    return None


async def refresh_comment_reaction_counts(comment: Comment, session: AsyncSession) -> None:
    like_result = await session.execute(
        select(func.count())
        .select_from(CommentReactionVote)
        .where(CommentReactionVote.comment_id == comment.id, CommentReactionVote.reaction == "like")
    )
    dislike_result = await session.execute(
        select(func.count())
        .select_from(CommentReactionVote)
        .where(CommentReactionVote.comment_id == comment.id, CommentReactionVote.reaction == "dislike")
    )
    comment.like_count = like_result.scalar_one()
    comment.dislike_count = dislike_result.scalar_one()

@router.post("/upload", response_model=PostRead)
async def upload_file(
    file: UploadFile = File(...), 
    caption: str = Form(...), 
    product_name: str = Form(...),
    product_category: str = Form(...),
    purchase_source: str = Form(...),
    purchase_date: date = Form(...),
    purchase_country: str = Form(...),
    rating: int = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Post:
    # Validate incoming form data using the schema
    try:
        post_data = PostCreate(
            caption=caption,
            product_name=product_name,
            product_category=product_category,
            purchase_source=purchase_source,
            purchase_date=purchase_date,
            purchase_country=purchase_country,
            rating=rating,
        )
    except ValidationError as exc:
        raise AppException(message="All product review fields are required", status_code=422, detail=exc.errors())

    # Basic validation for file types
    allowed_types = ["image/jpeg", "image/png", "video/mp4", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise AppException(message="Unsupported file type", status_code=415, detail=f"Allowed: {allowed_types}")

    file_type = "photo" if "image" in file.content_type else "video"

    try:
        content = await file.read()
        upload_info = await run_in_threadpool(
            upload_media,
            content=content,
            filename=file.filename,
        )
    except Exception as e:
        logger.exception(f"ImageKit upload failed for {file.filename}: {e}")
        raise AppException(message="Failed to upload to cloud storage", status_code=500)

    post = Post(
        caption=post_data.caption,
        url=upload_info.url,
        file_type=file_type,
        file_name=upload_info.file_name,
        file_id=upload_info.file_id,
        product_name=post_data.product_name,
        product_category=post_data.product_category,
        purchase_source=post_data.purchase_source,
        purchase_date=post_data.purchase_date,
        purchase_country=post_data.purchase_country,
        rating=post_data.rating,
        user_id=current_user.id,
    )

    try:
        session.add(post)
        await session.commit()
        await session.refresh(post)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Database save failed after ImageKit upload {upload_info.file_id}: {e}")
        try:
            await run_in_threadpool(delete_media, upload_info.file_id)
        except Exception as cleanup_error:
            logger.error(f"Failed to clean up ImageKit file {upload_info.file_id}: {cleanup_error}")
        raise AppException(message="Failed to save uploaded media", status_code=500)

    logger.info(f"Successfully uploaded {post.file_type}: {post.file_name} with ID {post.id}")
    return post

@router.get("/feed", response_model=List[PostRead])
async def get_feed(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
) -> List[Post]:
    """Fetch posts with pagination and optional search"""
    query = select(Post)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Post.caption.ilike(pattern),
                Post.product_name.ilike(pattern),
                Post.product_category.ilike(pattern),
                Post.purchase_source.ilike(pattern),
                Post.purchase_country.ilike(pattern),
            )
        )
        
    query = query.order_by(Post.created_at.desc()).offset(skip).limit(limit)
    
    result = await session.execute(query)
    posts = result.scalars().all()
    return posts


@router.get("/me", response_model=List[PostRead])
async def get_my_posts(
    limit: int = 6,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Post]:
    result = await session.execute(
        select(Post)
        .where(Post.user_id == current_user.id)
        .order_by(Post.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_posts(
    request: BulkDeleteRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BulkDeleteResponse:
    """Delete multiple posts and their associated files from ImageKit"""
    # 1. Fetch posts to get their ImageKit file_ids
    result = await session.execute(select(Post).where(Post.id.in_(request.post_ids)))
    posts = result.scalars().all()

    if not posts:
        raise AppException(message="No matching posts found", status_code=404)
    if any(post.user_id != current_user.id for post in posts):
        raise AppException(message="You can only delete your own posts", status_code=403)

    # 2. Extract file_ids and perform bulk delete in ImageKit
    file_ids = [p.file_id for p in posts if p.file_id]
    if file_ids:
        background_tasks.add_task(bg_bulk_delete_imagekit_files, file_ids)

    # 3. Delete records from Database
    found_ids = [p.id for p in posts]
    await session.execute(
        delete(CommentReactionVote).where(
            CommentReactionVote.comment_id.in_(
                select(Comment.id).where(Comment.post_id.in_(found_ids))
            )
        )
    )
    await session.execute(delete(Comment).where(Comment.post_id.in_(found_ids)))
    await session.execute(delete(Post).where(Post.id.in_(found_ids)))
    await session.commit()

    logger.warning(f"Bulk deleted {len(found_ids)} posts from database")
    return {"status": "success", "deleted_count": len(found_ids)}


@router.get("/{post_id}/comments", response_model=List[CommentRead])
async def get_post_comments(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
    anonymous_id: Optional[str] = Header(None, alias="X-Anonymous-Id"),
) -> List[CommentRead]:
    result = await session.execute(
        select(Comment, User)
        .outerjoin(User, User.id == Comment.user_id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
    )
    comment_rows = result.all()
    comment_ids = [comment.id for comment, _ in comment_rows]
    reaction_by_comment_id: dict[str, str] = {}

    if comment_ids:
        reaction_query = select(CommentReactionVote).where(CommentReactionVote.comment_id.in_(comment_ids))
        if current_user:
            if anonymous_id:
                reaction_query = reaction_query.where(
                    or_(
                        CommentReactionVote.user_id == current_user.id,
                        CommentReactionVote.anonymous_id == anonymous_id,
                    )
                )
            else:
                reaction_query = reaction_query.where(CommentReactionVote.user_id == current_user.id)
        elif anonymous_id:
            reaction_query = reaction_query.where(CommentReactionVote.anonymous_id == anonymous_id)
        else:
            reaction_query = None

        if reaction_query is not None:
            reaction_result = await session.execute(reaction_query)
            for reaction in reaction_result.scalars().all():
                if reaction.user_id == (current_user.id if current_user else None):
                    reaction_by_comment_id[reaction.comment_id] = reaction.reaction
                elif reaction.comment_id not in reaction_by_comment_id:
                    reaction_by_comment_id[reaction.comment_id] = reaction.reaction

    return [
        to_comment_read(comment, user, reaction_by_comment_id.get(comment.id))
        for comment, user in comment_rows
    ]


@router.post("/{post_id}/comments", response_model=CommentRead, status_code=201)
async def create_post_comment(
    post_id: str,
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> CommentRead:
    post_result = await session.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalar_one_or_none():
        raise AppException(message="Post not found", status_code=404)

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id if current_user else None,
        content=comment_data.content.strip(),
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return to_comment_read(comment, current_user)


@router.patch("/comments/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: str,
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise AppException(message="Comment not found", status_code=404)
    if comment.user_id != current_user.id:
        raise AppException(message="You can only edit your own comment", status_code=403)
    if not can_change_comment(comment):
        raise AppException(message="Comments can only be edited within 15 minutes", status_code=403)

    comment.content = comment_data.content.strip()
    comment.updated_at = datetime.now()
    await session.commit()
    await session.refresh(comment)
    return to_comment_read(comment, current_user)


@router.post("/comments/{comment_id}/reaction", response_model=CommentRead)
async def react_to_comment(
    comment_id: str,
    reaction_data: CommentReaction,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
    anonymous_id: Optional[str] = Header(None, alias="X-Anonymous-Id"),
) -> CommentRead:
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise AppException(message="Comment not found", status_code=404)

    actor_filter = reaction_actor_filter(comment_id, current_user, anonymous_id)
    if actor_filter is None:
        raise AppException(message="Reaction session is missing", status_code=400)

    existing_result = await session.execute(select(CommentReactionVote).where(*actor_filter))
    existing_reaction = existing_result.scalar_one_or_none()

    if current_user and anonymous_id:
        anonymous_result = await session.execute(
            select(CommentReactionVote).where(
                CommentReactionVote.comment_id == comment_id,
                CommentReactionVote.anonymous_id == anonymous_id,
            )
        )
        anonymous_reaction = anonymous_result.scalar_one_or_none()
        if anonymous_reaction and existing_reaction:
            await session.delete(anonymous_reaction)
        elif anonymous_reaction and not existing_reaction:
            anonymous_reaction.user_id = current_user.id
            anonymous_reaction.anonymous_id = None
            existing_reaction = anonymous_reaction

    if existing_reaction:
        existing_reaction.reaction = reaction_data.reaction
        existing_reaction.updated_at = datetime.now()
    else:
        session.add(
            CommentReactionVote(
                comment_id=comment.id,
                user_id=current_user.id if current_user else None,
                anonymous_id=None if current_user else anonymous_id,
                reaction=reaction_data.reaction,
            )
        )

    await refresh_comment_reaction_counts(comment, session)
    comment.updated_at = datetime.now()
    await session.commit()
    await session.refresh(comment)

    user = None
    if comment.user_id:
        user_result = await session.execute(select(User).where(User.id == comment.user_id))
        user = user_result.scalar_one_or_none()
    return to_comment_read(comment, user, reaction_data.reaction)


@router.delete("/comments/{comment_id}", response_model=DeleteResponse)
async def delete_comment(
    comment_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> DeleteResponse:
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise AppException(message="Comment not found", status_code=404)

    if comment.user_id is None:
        post_result = await session.execute(select(Post).where(Post.id == comment.post_id))
        post = post_result.scalar_one_or_none()
        if not post or post.user_id != current_user.id:
            raise AppException(message="Only the post owner can delete anonymous comments", status_code=403)
    else:
        if comment.user_id != current_user.id:
            raise AppException(message="You can only delete your own comment", status_code=403)
        if not can_change_comment(comment):
            raise AppException(message="Comments can only be deleted within 15 minutes", status_code=403)

    await session.execute(delete(CommentReactionVote).where(CommentReactionVote.comment_id == comment_id))
    await session.execute(delete(Comment).where(Comment.id == comment_id))
    await session.commit()
    return {"status": "success", "message": f"Comment {comment_id} deleted"}

@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> Post:
    """Fetch a single post by ID"""
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise AppException(message="Post not found", status_code=404)
    return post

@router.delete("/{post_id}", response_model=DeleteResponse)
async def delete_post(
    post_id: str, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> DeleteResponse:
    """Delete a post by ID"""
    # Check if exists
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise AppException(message="Post not found", status_code=404)
    if post.user_id != current_user.id:
        raise AppException(message="You can only delete your own posts", status_code=403)
    
    # Delete the file from ImageKit if file_id exists
    if post.file_id:
        background_tasks.add_task(bg_delete_imagekit_file, post.file_id)

    await session.execute(
        delete(CommentReactionVote).where(
            CommentReactionVote.comment_id.in_(
                select(Comment.id).where(Comment.post_id == post_id)
            )
        )
    )
    await session.execute(delete(Comment).where(Comment.post_id == post_id))
    await session.execute(delete(Post).where(Post.id == post_id))
    await session.commit()
    logger.warning(f"Deleted post and associated comments with ID {post_id}")
    
    return {"status": "success", "message": f"Post {post_id} deleted"}
