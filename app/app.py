from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.logger import logger
from contextlib import asynccontextmanager
from app.database.db import engine, Base
from app.core.config import settings
from app.api.routes.authRoutes import router as auth_router
from app.api.routes.postRoutes import router as post_router
from app.core.exceptions import AppException, app_exception_handler
from sqlalchemy import text


# Initialize database tables on startup
async def init_db():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                text(
                    "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS first_name VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS last_name VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS country VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS user_id VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS product_name VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS product_category VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS purchase_source VARCHAR"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS purchase_date DATE"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS purchase_country VARCHAR"
                )
            )
            await conn.execute(
                text("ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS rating INTEGER")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_posts_user_id ON public.posts (user_id)"
                )
            )
            await conn.execute(
                text("ALTER TABLE public.comments ALTER COLUMN user_id DROP NOT NULL")
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS like_count INTEGER NOT NULL DEFAULT 0"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS dislike_count INTEGER NOT NULL DEFAULT 0"
                )
            )
            await conn.execute(
                text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'ck_comments_like_count_non_negative'
                    ) THEN
                        ALTER TABLE public.comments
                        ADD CONSTRAINT ck_comments_like_count_non_negative CHECK (like_count >= 0);
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'ck_comments_dislike_count_non_negative'
                    ) THEN
                        ALTER TABLE public.comments
                        ADD CONSTRAINT ck_comments_dislike_count_non_negative CHECK (dislike_count >= 0);
                    END IF;
                END $$;
            """)
            )
            await conn.execute(
                text("ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text("""
                DO $$
                DECLARE
                    app_role text := current_user;
                BEGIN
                    DROP POLICY IF EXISTS comments_backend_all ON public.comments;
                    EXECUTE format(
                        'CREATE POLICY comments_backend_all ON public.comments FOR ALL TO %I USING (true) WITH CHECK (true)',
                        app_role
                    );
                END $$;
            """)
            )
            await conn.execute(
                text("ALTER TABLE public.comments FORCE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text("ALTER TABLE public.comment_reactions ENABLE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text("""
                DO $$
                DECLARE
                    app_role text := current_user;
                BEGIN
                    DROP POLICY IF EXISTS comment_reactions_backend_all ON public.comment_reactions;
                    EXECUTE format(
                        'CREATE POLICY comment_reactions_backend_all ON public.comment_reactions FOR ALL TO %I USING (true) WITH CHECK (true)',
                        app_role
                    );
                END $$;
            """)
            )
            await conn.execute(
                text("ALTER TABLE public.comment_reactions FORCE ROW LEVEL SECURITY")
            )
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application")

    await init_db()
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            logger.info("Connected to database successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")
    await engine.dispose()


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_exception_handler(AppException, app_exception_handler)


@app.get("/health")
async def health_check():
    checks = {
        "database": False,
        "routes": False,
    }
    errors = {}

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        errors["database"] = str(e)

    expected_routes = {
        "/posts/upload",
        "/posts/feed",
        "/posts/me",
        "/posts/bulk-delete",
        "/posts/{post_id}/comments",
        "/posts/comments/{comment_id}/reaction",
        "/posts/comments/{comment_id}",
        "/posts/{post_id}",
        "/auth/register",
        "/auth/login",
        "/auth/me",
    }
    registered_routes = {route.path for route in app.routes}
    missing_routes = sorted(expected_routes - registered_routes)
    if missing_routes:
        errors["routes"] = f"Missing routes: {', '.join(missing_routes)}"
    else:
        checks["routes"] = True

    is_healthy = all(checks.values())
    content = {
        "status": "okay" if is_healthy else "not okay",
        "checks": checks,
    }
    if errors:
        content["errors"] = errors

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content=content,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post_router, prefix="/posts", tags=["Posts"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
