from __future__ import annotations

from datetime import date, datetime
from html import escape
import os
from pathlib import Path
import re
import uuid
from typing import Any

import requests
import streamlit as st


LOCAL_API_URL_FILE = Path(".local_api_url")


def default_api_base_url() -> str:
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    if LOCAL_API_URL_FILE.exists():
        local_url = LOCAL_API_URL_FILE.read_text(encoding="utf-8").strip()
        if local_url:
            return local_url.rstrip("/")
    return "http://localhost:8000"


DEFAULT_API_BASE_URL = default_api_base_url()
IMAGE_TYPES = {"photo", "image"}
VIDEO_TYPES = {"video"}
URL_PATTERN = re.compile(r"(https?://[^\s<]+)")
PRODUCT_CATEGORIES = [
    "Apparel",
    "Food",
    "Cosmetics",
    "Electronics",
    "Home",
    "Health",
    "Books",
    "Sports",
    "Other",
]
REVIEW_FORM_KEYS = [
    "review_upload_file",
    "review_product_name",
    "review_product_category",
    "review_purchase_source",
    "review_purchase_date",
    "review_purchase_country",
    "review_rating",
    "review_caption",
]


st.set_page_config(
    page_title="Product Review Forum",
    page_icon="PR",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #f6f8fb;
            --ink: #111827;
            --muted: #64748b;
            --line: #e2e8f0;
            --panel: #ffffff;
            --panel-soft: #f8fafc;
            --accent: #2563eb;
            --accent-dark: #1d4ed8;
            --success: #16a34a;
            --danger: #dc2626;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 30rem),
                linear-gradient(180deg, #f8fafc 0%, var(--app-bg) 45%, #eef2f7 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }

        [data-testid="stSidebar"] {
            background: #0f172a;
        }

        [data-testid="stSidebar"] * {
            color: #e5e7eb;
        }

        [data-testid="stSidebar"] input {
            color: #111827;
        }

        .sidebar-brand {
            margin: 10px 0 22px;
        }

        .sidebar-brand-title {
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .sidebar-brand-copy {
            color: #94a3b8;
            font-size: .9rem;
            line-height: 1.45;
        }

        .sidebar-account {
            border-top: 1px solid rgba(148, 163, 184, .18);
            padding-top: 18px;
            margin-top: 18px;
        }

        .sidebar-label {
            color: #94a3b8;
            font-size: .74rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .sidebar-user {
            color: #ffffff;
            font-size: .98rem;
            font-weight: 800;
            margin-bottom: 14px;
            word-break: break-word;
        }

        .sidebar-bottom-spacer {
            height: 14vh;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #172554 58%, #1d4ed8 100%);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            padding: 18px 22px;
            color: white;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
            position: relative;
        }

        .hero-label {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.16);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .08em;
        }

        .hero h1 {
            margin: 8px 0 5px;
            font-size: clamp(1.65rem, 3vw, 2.4rem);
            line-height: 1;
            color: white;
        }

        .hero p {
            margin: 0;
            max-width: 760px;
            color: #cbd5e1;
            font-size: .92rem;
        }

        .hero-highlight {
            color: #fde68a;
            font-weight: 900;
        }

        .hero-signout {
            position: absolute;
            top: 16px;
            right: 22px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 150px;
            min-height: 40px;
            border-radius: 10px;
            background: var(--accent);
            border: 1px solid var(--accent);
            color: #ffffff !important;
            font-weight: 800;
            text-decoration: none !important;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.26);
        }

        .hero-signout:hover {
            background: var(--success);
            border-color: var(--success);
            color: #ffffff !important;
        }

        div[data-testid="stAppViewContainer"],
        div[data-testid="stMain"],
        div[data-testid="stMainBlockContainer"],
        .block-container,
        div[data-testid="stVerticalBlock"] {
            overflow: visible !important;
        }

        div[data-testid="stElementContainer"]:has(.st-key-reviews_filter_bar),
        div[data-testid="stElementContainer"]:has(.st-key-my_reviews_filter_bar),
        div[data-testid="stElementContainer"]:has(.st-key-reviews-filter-bar),
        div[data-testid="stElementContainer"]:has(.st-key-my-reviews-filter-bar),
        .element-container:has(.st-key-reviews_filter_bar),
        .element-container:has(.st-key-my_reviews_filter_bar),
        .element-container:has(.st-key-reviews-filter-bar),
        .element-container:has(.st-key-my-reviews-filter-bar) {
            display: contents;
        }

        .st-key-feed_page_shell,
        .st-key-my_reviews_page_shell,
        .st-key-feed-page-shell,
        .st-key-my-reviews-page-shell {
            overflow: visible !important;
        }

        .st-key-reviews_filter_bar,
        .st-key-my_reviews_filter_bar,
        .st-key-reviews-filter-bar,
        .st-key-my-reviews-filter-bar {
            align-self: stretch;
            position: sticky !important;
            position: -webkit-sticky !important;
            top: 0.35rem;
            z-index: 1001;
            background: rgba(248, 250, 252, .96);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 8px 0 10px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        }

        .st-key-reviews_filter_bar [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-my_reviews_filter_bar [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-reviews-filter-bar [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-my-reviews-filter-bar [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, .96);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: .82rem;
            font-weight: 700;
            border: 1px solid var(--line);
            background: var(--panel);
        }

        .status-ok {
            color: #047857;
            background: #ecfdf5;
            border-color: #bbf7d0;
        }

        .status-bad {
            color: #b91c1c;
            background: #fef2f2;
            border-color: #fecaca;
        }

        .surface {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }

        .section-title {
            font-size: .78rem;
            font-weight: 800;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: 4px;
        }

        .metric-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px 18px;
        }

        .metric-label {
            color: var(--muted);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .07em;
        }

        .metric-value {
            color: var(--ink);
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1.1;
            margin-top: 4px;
        }

        .metric-value.session-value {
            font-size: .95rem;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .media-card {
            border: 1px solid var(--line);
            border-radius: 12px;
            overflow: hidden;
            background: var(--panel);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
            margin-bottom: 8px;
        }

        .feed-thumb {
            display: block;
            width: 100%;
            height: 135px;
            object-fit: cover;
            background: #e2e8f0;
        }

        video.feed-thumb {
            object-fit: cover;
        }

        .media-meta {
            padding: 9px 10px 10px;
        }

        .feed-meta {
            height: 168px;
            overflow: hidden;
        }

        .media-title {
            font-weight: 800;
            color: var(--ink);
            font-size: .92rem;
            line-height: 1.2;
            margin-bottom: 4px;
        }

        .media-sub {
            color: var(--muted);
            font-size: .76rem;
            line-height: 1.3;
        }

        .rating-stars {
            color: #f59e0b;
            font-weight: 900;
            letter-spacing: .04em;
        }

        .type-chip {
            display: inline-flex;
            border-radius: 999px;
            padding: 4px 8px;
            background: #eff6ff;
            color: #1d4ed8;
            font-size: .72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: 8px;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a,
        div[data-testid="stPopover"] button {
            border-radius: 10px;
            font-weight: 700;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stLinkButton > a,
        div[data-testid="stPopover"] button {
            background: var(--accent) !important;
            border: 1px solid var(--accent) !important;
            color: #ffffff !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22);
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stLinkButton > a:hover,
        div[data-testid="stPopover"] button:hover {
            background: var(--success) !important;
            border-color: var(--success) !important;
            color: #ffffff !important;
        }

        div[data-testid="stForm"]:has(textarea[aria-label="Add a comment"]) button,
        div[data-testid="stForm"]:has(textarea[aria-label="Edit comment"]) button,
        div[data-testid="stButton"]:has(button[kind="secondary"]) button[aria-label*="Delete comment"],
        div[data-testid="stButton"] button[aria-label="x"] {
            background: var(--danger) !important;
            border-color: var(--danger) !important;
            color: #ffffff !important;
            min-height: 2.15rem;
            width: 2.35rem;
            padding: 0.2rem 0.45rem;
            font-size: 0.82rem;
            box-shadow: 0 6px 14px rgba(220, 38, 38, 0.20);
        }

        div[data-testid="stForm"]:has(textarea[aria-label="Add a comment"]) button p,
        div[data-testid="stForm"]:has(textarea[aria-label="Edit comment"]) button p {
            font-size: 1rem;
            line-height: 1;
        }

        .comment-card {
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 10px 12px;
            margin-bottom: 10px;
            background: #ffffff;
        }

        .comment-author {
            font-weight: 800;
            color: var(--ink);
            margin-bottom: 4px;
        }

        .comment-body {
            color: #334155;
            font-size: .92rem;
            line-height: 1.45;
            margin-bottom: 6px;
        }

        .comment-body a {
            color: var(--accent-dark);
            font-weight: 700;
            text-decoration: underline;
        }

        div[class*="st-key-like_"] button,
        div[class*="st-key-like-"] button,
        div[class*="st-key-dislike_"] button,
        div[class*="st-key-dislike-"] button {
            min-height: 1.85rem;
            padding: 0.1rem 0.45rem;
            border-radius: 999px;
            font-size: .78rem;
            box-shadow: none;
        }

        div[class*="st-key-like_"] button[kind="secondary"],
        div[class*="st-key-like-"] button[kind="secondary"],
        div[class*="st-key-dislike_"] button[kind="secondary"],
        div[class*="st-key-dislike-"] button[kind="secondary"] {
            background: #f8fafc !important;
            border-color: var(--line) !important;
            color: #334155 !important;
        }

        div[class*="st-key-delete_comment_"] button,
        div[class*="st-key-delete-comment-"] button {
            min-height: 1.9rem;
            width: 2rem;
            padding: 0.1rem 0.25rem;
            border-radius: 999px;
            background: #fef2f2 !important;
            border-color: #fecaca !important;
            color: var(--danger) !important;
            box-shadow: none;
        }

        div[class*="st-key-delete_comment_"] button:hover,
        div[class*="st-key-delete-comment-"] button:hover {
            background: var(--danger) !important;
            border-color: var(--danger) !important;
            color: #ffffff !important;
        }

        div[data-testid="stRadio"] label p {
            color: #f59e0b;
            font-weight: 900;
            letter-spacing: .06em;
        }

        div[data-testid="stFileUploader"] {
            border: 1px dashed #93c5fd;
            border-radius: 14px;
            padding: 8px;
            background: #eff6ff;
        }

        .small-muted {
            color: var(--muted);
            font-size: .85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    current_api_url = st.session_state.get("api_base_url", "")
    if not current_api_url or (
        current_api_url.startswith("http://localhost:800")
        and current_api_url != DEFAULT_API_BASE_URL
    ):
        st.session_state.api_base_url = DEFAULT_API_BASE_URL
    st.session_state.setdefault("access_token", "")
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("anonymous_id", str(uuid.uuid4()))
    st.session_state.setdefault("selected_post_id", "")
    st.session_state.setdefault("current_view", "feed")


def api_url(path: str) -> str:
    return f"{st.session_state.api_base_url.rstrip('/')}{path}"


def auth_headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def interaction_headers() -> dict[str, str]:
    headers = auth_headers()
    headers["X-Anonymous-Id"] = st.session_state.get("anonymous_id", "")
    return headers


@st.cache_resource
def get_http_session() -> requests.Session:
    return requests.Session()


def _read_response_error(response: requests.Response) -> Any:
    try:
        payload = response.json()
    except ValueError:
        return response.text
    if isinstance(payload, dict):
        return payload.get("message") or payload.get("detail") or response.text
    return payload


def _validation_field_names(message: Any) -> list[str]:
    if not isinstance(message, list):
        return []

    names: list[str] = []
    for item in message:
        if not isinstance(item, dict):
            continue
        loc = item.get("loc")
        if isinstance(loc, list) and loc:
            field = str(loc[-1]).replace("_", " ")
            if field not in names:
                names.append(field)
    return names


def friendly_error_message(status_code: int, message: Any) -> str:
    field_names = _validation_field_names(message)
    if field_names:
        return f"Please check these fields: {', '.join(field_names)}."

    clean_message = str(message or "").strip()
    if clean_message and clean_message.lower() not in {"null", "none"}:
        if status_code == 422:
            return "Please check the required fields and try again."
        return clean_message

    if status_code == 400:
        return "Please check your information and try again."
    if status_code == 401:
        return "Please sign in with a valid email and password."
    if status_code == 403:
        return "You do not have permission to do that."
    if status_code == 404:
        return "That item could not be found."
    if status_code == 409:
        return "This information already exists."
    if status_code >= 500:
        return "Something went wrong on the server. Please try again."
    return "Something went wrong. Please try again."


def request_json(
    method: str, path: str, **kwargs: Any
) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    try:
        response = get_http_session().request(
            method, api_url(path), timeout=30, **kwargs
        )
    except requests.RequestException:
        return (
            None,
            "Could not connect to the service. Please make sure the backend is running.",
        )

    if response.status_code >= 400:
        message = _read_response_error(response)
        return None, friendly_error_message(response.status_code, message)

    if not response.content:
        return {}, None
    return response.json(), None


@st.cache_data(ttl=20, show_spinner=False)
def cached_get_json(
    api_base_url: str,
    path: str,
    params: tuple[tuple[str, Any], ...] = (),
    token: str = "",
    anonymous_id: str = "",
) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if anonymous_id:
        headers["X-Anonymous-Id"] = anonymous_id
    try:
        response = get_http_session().get(
            f"{api_base_url.rstrip('/')}{path}",
            params=dict(params),
            headers=headers,
            timeout=20,
        )
    except requests.RequestException:
        return (
            None,
            "Could not connect to the service. Please make sure the backend is running.",
        )

    if response.status_code >= 400:
        message = _read_response_error(response)
        return None, friendly_error_message(response.status_code, message)

    if not response.content:
        return {}, None
    return response.json(), None


def clear_read_cache() -> None:
    cached_get_json.clear()


def format_date(value: str | None) -> str:
    if not value:
        return "Unknown date"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
            "%d %b %Y, %I:%M %p"
        )
    except ValueError:
        return value


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def compact_date(value: str | None) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d %b %Y") if parsed else "Not provided"


def normalize_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_form_data(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def clear_review_form_state() -> None:
    for key in REVIEW_FORM_KEYS:
        st.session_state.pop(key, None)


def validate_review_form(
    uploaded_file: Any,
    caption: str,
    product_name: str,
    product_category: str,
    purchase_source: str,
    purchase_date: date | None,
    purchase_country: str,
    rating: int,
) -> list[str]:
    missing = []
    if uploaded_file is None:
        missing.append("product image or video")
    if not normalize_optional(product_name):
        missing.append("product name")
    if not normalize_optional(product_category):
        missing.append("product category")
    if not normalize_optional(purchase_source):
        missing.append("purchased from")
    if purchase_date is None:
        missing.append("purchased date")
    if not normalize_optional(purchase_country):
        missing.append("purchased in country")
    if rating not in {1, 2, 3, 4, 5}:
        missing.append("star rating")
    if not normalize_optional(caption):
        missing.append("review")
    return missing


def show_missing_review_fields_popup(missing: list[str]) -> None:
    def render_content() -> None:
        st.warning("Please complete the missing information before publishing.")
        for field in missing:
            st.markdown(f"- {field.title()}")
        if st.button("OK", width="stretch"):
            st.rerun()

    if hasattr(st, "dialog"):

        @st.dialog("Complete required fields")
        def missing_fields_dialog() -> None:
            render_content()

        missing_fields_dialog()
    else:
        render_content()


def rating_stars(value: Any) -> str:
    try:
        rating = max(1, min(5, int(value)))
    except (TypeError, ValueError):
        return "Not rated"
    return f"{'★' * rating}{'☆' * (5 - rating)}"


def rating_options() -> list[str]:
    return [rating_stars(value) for value in range(1, 6)]


def rating_from_stars(value: str) -> int:
    return max(1, min(5, value.count("★")))


def linkify_comment(value: str | None) -> str:
    escaped = escape(value or "")

    def replace(match: re.Match[str]) -> str:
        url = match.group(0)
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'

    return URL_PATTERN.sub(replace, escaped).replace("\n", "<br>")


def post_title(post: dict[str, Any]) -> str:
    return post.get("product_name") or "Product review"


def product_details_html(post: dict[str, Any]) -> str:
    details = [
        ("Product name", post.get("product_name") or "Not provided"),
        ("Category", post.get("product_category") or "Not provided"),
        ("Purchased from", post.get("purchase_source") or "Not provided"),
        ("Purchase date", compact_date(post.get("purchase_date"))),
        ("Country", post.get("purchase_country") or "Not provided"),
        (
            "Rating",
            f'<span class="rating-stars">{rating_stars(post.get("rating"))}</span>',
        ),
    ]
    rows = "".join(
        f'<div class="media-sub"><strong>{escape(label)}:</strong> {value if label == "Rating" else escape(str(value))}</div>'
        for label, value in details
    )
    caption = post.get("caption")
    if caption:
        rows += f'<div class="media-sub"><strong>Review:</strong> {escape(truncate(caption, 120))}</div>'
    return rows


def truncate(value: str | None, limit: int = 62) -> str:
    text = value or "Untitled"
    return text if len(text) <= limit else f"{text[: limit - 1]}..."


def user_display_name(user: dict[str, Any] | None) -> str:
    if not user:
        return "Guest"
    full_name = " ".join(
        part for part in [user.get("first_name"), user.get("last_name")] if part
    )
    return full_name or user.get("email", "User")


def is_edit_window_open(value: str | None) -> bool:
    if not value:
        return False
    try:
        editable_until = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return False
    return datetime.now() <= editable_until


def render_media(post: dict[str, Any], *, use_thumbnail: bool = False) -> None:
    file_type = post.get("file_type", "")
    url = post.get("thumbnail_url") if use_thumbnail else post.get("url")
    url = url or post.get("url")

    if file_type in IMAGE_TYPES:
        st.image(url, width="stretch")
    elif file_type in VIDEO_TYPES:
        if use_thumbnail:
            st.markdown(
                f'<video class="feed-thumb" src="{escape(post.get("url") or "", quote=True)}#t=0.1" muted preload="metadata"></video>',
                unsafe_allow_html=True,
            )
        else:
            st.video(post.get("url"))
    else:
        st.link_button("Open media", post.get("url", "#"), width="stretch")


def render_feed_thumbnail(post: dict[str, Any]) -> None:
    url = post.get("thumbnail_url") or post.get("url") or ""
    if not url:
        st.markdown('<div class="feed-thumb"></div>', unsafe_allow_html=True)
        return
    if post.get("file_type") in VIDEO_TYPES:
        st.markdown(
            f'<video class="feed-thumb" src="{escape(post.get("url") or url, quote=True)}#t=0.1" muted preload="metadata"></video>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<img class="feed-thumb" src="{escape(url, quote=True)}" alt="Product review media thumbnail">',
            unsafe_allow_html=True,
        )


def register_user(email: str, password: str) -> None:
    email = email.strip()
    if not email or not password:
        st.error("Enter an email and password to create your account.")
        return
    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    payload, error = request_json(
        "POST", "/auth/register", json={"email": email, "password": password}
    )
    if error:
        st.error(error)
        return

    st.session_state.access_token = payload["access_token"]
    st.session_state.current_user = payload["user"]
    clear_read_cache()
    st.success("Account created and signed in.")
    st.rerun()


def login_user(email: str, password: str) -> None:
    email = email.strip()
    if not email or not password:
        st.error("Enter your email and password to sign in.")
        return

    payload, error = request_json(
        "POST", "/auth/login", data={"username": email, "password": password}
    )
    if error:
        st.error(error)
        return

    st.session_state.access_token = payload["access_token"]
    user, user_error = request_json("GET", "/auth/me", headers=auth_headers())
    st.session_state.current_user = {"email": email} if user_error else user
    clear_read_cache()
    st.success("Signed in.")
    st.rerun()


def update_profile(first_name: str, last_name: str, country: str) -> None:
    payload, error = request_json(
        "PATCH",
        "/auth/me",
        headers=auth_headers(),
        json={
            "first_name": first_name.strip() or None,
            "last_name": last_name.strip() or None,
            "country": country.strip() or None,
        },
    )
    if error:
        st.error(error)
        return
    st.session_state.current_user = payload
    clear_read_cache()
    st.success("Profile updated.")
    st.rerun()


def logout_user() -> None:
    st.session_state.access_token = ""
    st.session_state.current_user = None
    st.session_state.selected_post_id = ""
    st.session_state.current_view = "feed"
    try:
        st.query_params.clear()
    except AttributeError:
        pass
    clear_read_cache()
    st.rerun()


def handle_query_actions() -> None:
    logout_value = st.query_params.get("logout")
    if logout_value == "1" or logout_value == ["1"]:
        logout_user()


def fetch_feed(search: str = "", limit: int = 40) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"skip": 0, "limit": limit}
    if search:
        params["search"] = search
    payload, error = cached_get_json(
        st.session_state.api_base_url,
        "/posts/feed",
        tuple(sorted(params.items())),
    )
    if error:
        st.error(error)
        return []
    return payload if isinstance(payload, list) else []


def fetch_my_posts(limit: int = 40) -> list[dict[str, Any]]:
    if not st.session_state.get("access_token"):
        return []
    payload, error = cached_get_json(
        st.session_state.api_base_url,
        "/posts/me",
        (("limit", limit),),
        st.session_state.access_token,
    )
    if error:
        return []
    return payload if isinstance(payload, list) else []


def fetch_comments(post_id: str) -> list[dict[str, Any]]:
    payload, error = cached_get_json(
        st.session_state.api_base_url,
        f"/posts/{post_id}/comments",
        token=st.session_state.get("access_token", ""),
        anonymous_id=st.session_state.get("anonymous_id", ""),
    )
    if error:
        st.warning(error)
        return []
    return payload if isinstance(payload, list) else []


def create_comment(post_id: str, content: str) -> dict[str, Any] | None:
    if not content.strip():
        st.error("Enter a comment before posting.")
        return None
    payload, error = request_json(
        "POST",
        f"/posts/{post_id}/comments",
        headers=interaction_headers(),
        json={"content": content.strip()},
    )
    if error:
        st.error(error)
        return None
    st.success("Comment added.")
    return payload if isinstance(payload, dict) else None


def react_to_comment(comment_id: str, reaction: str) -> bool:
    _, error = request_json(
        "POST",
        f"/posts/comments/{comment_id}/reaction",
        headers=interaction_headers(),
        json={"reaction": reaction},
    )
    if error:
        st.error(error)
        return False
    clear_read_cache()
    return True


def update_comment(comment_id: str, content: str) -> bool:
    _, error = request_json(
        "PATCH",
        f"/posts/comments/{comment_id}",
        headers=auth_headers(),
        json={"content": content.strip()},
    )
    if error:
        st.error(error)
        return False
    clear_read_cache()
    st.success("Comment updated.")
    return True


def delete_comment(comment_id: str) -> bool:
    _, error = request_json(
        "DELETE", f"/posts/comments/{comment_id}", headers=auth_headers()
    )
    if error:
        st.error(error)
        return False
    clear_read_cache()
    st.success("Comment deleted.")
    return True


def upload_post(
    uploaded_file: Any,
    caption: str,
    product_name: str,
    product_category: str,
    purchase_source: str,
    purchase_date: date | None,
    purchase_country: str,
    rating: int,
) -> None:
    missing = validate_review_form(
        uploaded_file,
        caption,
        product_name,
        product_category,
        purchase_source,
        purchase_date,
        purchase_country,
        rating,
    )
    if missing:
        show_missing_review_fields_popup(missing)
        return

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    payload, error = request_json(
        "POST",
        "/posts/upload",
        headers=auth_headers(),
        files=files,
        data=clean_form_data(
            {
                "caption": caption,
                "product_name": normalize_optional(product_name),
                "product_category": normalize_optional(product_category),
                "purchase_source": normalize_optional(purchase_source),
                "purchase_date": purchase_date.isoformat() if purchase_date else None,
                "purchase_country": normalize_optional(purchase_country),
                "rating": rating,
            }
        ),
    )
    if error:
        st.error(error)
        return

    clear_review_form_state()
    st.session_state.selected_post_id = payload["id"]
    st.session_state.current_view = "manage"
    clear_read_cache()
    st.success("Your product review was posted.")
    st.rerun()


def delete_post(post_id: str) -> None:
    _, error = request_json("DELETE", f"/posts/{post_id}", headers=auth_headers())
    if error:
        st.error(error)
        return
    st.session_state.selected_post_id = ""
    st.session_state.current_view = "feed"
    clear_read_cache()
    st.success("Post deleted.")
    st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Product Review Forum</div>
                <div class="sidebar-brand-copy">Share product photos, videos, and short reviews.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user = st.session_state.get("current_user")
        if user:
            st.markdown(
                f"""
                <div class="sidebar-account">
                    <div class="sidebar-label">Account</div>
                    <div class="sidebar-user">Signed in as: {escape(user_display_name(user))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Feed", width="stretch"):
                st.session_state.current_view = "feed"
                st.session_state.selected_post_id = ""
                st.rerun()

            if st.button("Add review", width="stretch"):
                st.session_state.current_view = "create"
                st.session_state.selected_post_id = ""
                st.rerun()

            if st.button("Your reviews", width="stretch"):
                st.session_state.current_view = "my_reviews"
                st.session_state.selected_post_id = ""
                st.rerun()

            st.markdown(
                '<div class="sidebar-bottom-spacer"></div>', unsafe_allow_html=True
            )
            profile_col, signout_col = st.columns(2, gap="small")
            with profile_col:
                with st.popover("Profile", use_container_width=True):
                    with st.form("profile_form"):
                        st.text_input(
                            "Email", value=user.get("email", ""), disabled=True
                        )
                        first_name = st.text_input(
                            "First name", value=user.get("first_name") or ""
                        )
                        last_name = st.text_input(
                            "Last name", value=user.get("last_name") or ""
                        )
                        country = st.text_input(
                            "Country", value=user.get("country") or ""
                        )
                        submitted = st.form_submit_button("Update", width="stretch")
                    if submitted:
                        update_profile(first_name, last_name, country)
            with signout_col:
                if st.button("Sign out", key="sidebar_signout", width="stretch"):
                    logout_user()
            return

        st.markdown("#### Access")
        tab_login, tab_register = st.tabs(["Login", "Register"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input(
                    "Password", type="password", key="login_password"
                )
                submitted = st.form_submit_button("Login", width="stretch")
            if submitted:
                login_user(email, password)

        with tab_register:
            with st.form("register_form"):
                email = st.text_input("Email", key="register_email")
                password = st.text_input(
                    "Password", type="password", key="register_password"
                )
                submitted = st.form_submit_button("Create account", width="stretch")
            if submitted:
                register_user(email, password)


def render_hero() -> None:
    signout_link = (
        '<a class="hero-signout" href="?logout=1" target="_self">Sign out</a>'
        if st.session_state.get("access_token")
        else ""
    )
    hero_html = (
        '<div class="hero">'
        f"{signout_link}"
        '<div class="hero-label">Community reviews</div>'
        "<h1>Product Review Forum</h1>"
        "<p>"
        '<span class="hero-highlight">Reviews matter.</span> '
        "Browse product photos and videos, read short reviews, and login to share "
        "your own product experience with the community."
        "</p>"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)


def render_metrics(posts: list[dict[str, Any]]) -> None:
    total = len(posts)
    photos = sum(1 for post in posts if post.get("file_type") in IMAGE_TYPES)
    videos = sum(1 for post in posts if post.get("file_type") in VIDEO_TYPES)
    session_state = (
        f"Signed in as: {user_display_name(st.session_state.get('current_user'))}"
        if st.session_state.get("access_token")
        else "Guest view"
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    metrics = [
        ("Visible posts", str(total)),
        ("Images", str(photos)),
        ("Videos", str(videos)),
        ("Session", session_state),
    ]
    for col, (label, value) in zip((c1, c2, c3, c4), metrics):
        with col:
            value_class = (
                "metric-value session-value" if label == "Session" else "metric-value"
            )
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="{value_class}">{escape(value)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_upload_panel() -> None:
    st.markdown(
        '<div class="section-title">Create review</div>', unsafe_allow_html=True
    )
    with st.container(border=True):
        st.subheader("Post a product review")
        st.caption("Add a product image or video and write a short review.")
        if not st.session_state.get("access_token"):
            st.info("Login to create product reviews.")
            return

        with st.form("upload_form"):
            uploaded_file = st.file_uploader(
                "Product image or video",
                type=["jpg", "jpeg", "png", "mp4", "mov"],
                key="review_upload_file",
            )
            product_name = st.text_input(
                "Product name",
                placeholder="Product name",
                key="review_product_name",
            )
            product_category = st.selectbox(
                "Product category",
                PRODUCT_CATEGORIES,
                key="review_product_category",
            )
            purchase_source = st.text_input(
                "Purchased from",
                placeholder="Online/offline merchant name",
                key="review_purchase_source",
            )
            purchase_date_value = st.date_input(
                "Purchased date",
                value=None,
                key="review_purchase_date",
            )
            purchase_country = st.text_input(
                "Purchased in country",
                placeholder="Country",
                key="review_purchase_country",
            )
            rating_choice = st.radio(
                "Star rating",
                rating_options(),
                index=4,
                horizontal=True,
                key="review_rating",
            )
            caption = st.text_area(
                "Review",
                max_chars=500,
                height=180,
                placeholder="What did you like or dislike?",
                key="review_caption",
            )
            submitted = st.form_submit_button("Publish review", width="stretch")
        if submitted:
            upload_post(
                uploaded_file,
                caption,
                product_name,
                product_category,
                purchase_source,
                purchase_date_value,
                purchase_country,
                rating_from_stars(rating_choice),
            )


def country_options_from_posts(posts: list[dict[str, Any]]) -> list[str]:
    countries = sorted(
        {post.get("purchase_country") for post in posts if post.get("purchase_country")}
    )
    return ["All", *countries]


def render_filters(
    posts: list[dict[str, Any]],
    *,
    key_prefix: str = "feed",
    title: str = "Reviews",
    include_country: bool = True,
) -> tuple[str, int, str, list[str], str]:
    filter_key = (
        "reviews_filter_bar" if key_prefix == "feed" else f"{key_prefix}_filter_bar"
    )
    with st.container(key=filter_key):
        st.markdown(
            f'<div class="section-title">{escape(title)}</div>', unsafe_allow_html=True
        )
        with st.container(border=True):
            column_spec = [2, 1, 1, 1.4, 1.2] if include_country else [2, 1, 1, 1.4]
            cols = st.columns(column_spec, gap="medium", vertical_alignment="bottom")
            with cols[0]:
                search = st.text_input(
                    "Search reviews",
                    placeholder=(
                        "Search category, merchant, country, or review..."
                        if include_country
                        else "Search product, category, merchant, or review..."
                    ),
                    help="Results update automatically as you type.",
                    key=f"{key_prefix}_search",
                )
            with cols[1]:
                limit = st.slider(
                    "Limit",
                    min_value=4,
                    max_value=40,
                    value=16,
                    step=4,
                    key=f"{key_prefix}_limit",
                )
            with cols[2]:
                media_filter = st.selectbox(
                    "Type", ["All", "Images", "Videos"], key=f"{key_prefix}_type"
                )
            with cols[3]:
                category_filter = st.multiselect(
                    "Category", PRODUCT_CATEGORIES, key=f"{key_prefix}_categories"
                )
            if include_country:
                country_options = country_options_from_posts(posts)
                current_country = st.session_state.get(f"{key_prefix}_country", "All")
                if current_country not in country_options:
                    st.session_state[f"{key_prefix}_country"] = "All"
                    current_country = "All"
                country_index = country_options.index(current_country)
                with cols[4]:
                    country_filter = st.selectbox(
                        "Country",
                        country_options,
                        index=country_index,
                        key=f"{key_prefix}_country",
                    )
            else:
                country_filter = "All"
    return search, limit, media_filter, category_filter, country_filter


def post_matches_search(post: dict[str, Any], search: str) -> bool:
    normalized_search = " ".join(search.split()).casefold()
    if not normalized_search:
        return True
    search_terms = normalized_search.split()
    searchable_values = [
        post_title(post),
        post.get("product_name"),
        post.get("product_category"),
        post.get("purchase_source"),
        post.get("purchase_country"),
        post.get("caption"),
    ]
    searchable_text = " ".join(
        str(value or "") for value in searchable_values
    ).casefold()
    return all(term in searchable_text for term in search_terms)


def filter_posts(
    posts: list[dict[str, Any]],
    media_filter: str,
    category_filter: list[str],
    country_filter: str,
    search: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    filtered = [post for post in posts if post_matches_search(post, search)]
    if media_filter == "Images":
        filtered = [post for post in filtered if post.get("file_type") in IMAGE_TYPES]
    elif media_filter == "Videos":
        filtered = [post for post in filtered if post.get("file_type") in VIDEO_TYPES]
    if category_filter:
        filtered = [
            post for post in filtered if post.get("product_category") in category_filter
        ]
    if country_filter != "All":
        filtered = [
            post for post in filtered if post.get("purchase_country") == country_filter
        ]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def render_feed(posts: list[dict[str, Any]]) -> None:
    if not posts:
        st.info("No posts found.")
        return

    cols = st.columns(4, gap="small")
    for index, post in enumerate(posts):
        with cols[index % 4]:
            st.markdown('<div class="media-card">', unsafe_allow_html=True)
            render_feed_thumbnail(post)
            st.markdown(
                f"""
                <div class="media-meta feed-meta">
                    <div class="media-title">{escape(post_title(post))}</div>
                    {product_details_html(post)}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("View comments", key=f"view_{post['id']}", width="stretch"):
                st.session_state.selected_post_id = post["id"]
                st.session_state.current_view = "manage"
                st.rerun()


def render_my_reviews() -> None:
    with st.container(key="my_reviews_page_shell"):
        posts = fetch_my_posts()
        search, limit, media_filter, category_filter, country_filter = render_filters(
            posts,
            key_prefix="my_reviews",
            title="Your reviews",
            include_country=False,
        )
        visible_posts = filter_posts(
            posts,
            media_filter,
            category_filter,
            country_filter,
            search=search,
            limit=limit,
        )
        if not posts:
            st.info("You have not added any reviews yet.")
            return
        render_metrics(visible_posts)
        st.write("")
        render_feed(visible_posts)


def render_selected_post() -> None:
    post_id = st.session_state.get("selected_post_id")
    if not post_id:
        return

    st.divider()
    st.markdown(
        '<div class="section-title">Review details</div>', unsafe_allow_html=True
    )

    payload, error = cached_get_json(
        st.session_state.api_base_url,
        f"/posts/{post_id}",
    )
    if error:
        st.warning(f"Could not load selected post. {error}")
        if st.button("Clear selection"):
            st.session_state.selected_post_id = ""
            st.session_state.current_view = "feed"
            st.rerun()
        return

    post = payload
    current_user = st.session_state.get("current_user") or {}

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        with st.container(border=True):
            render_media(post)
            st.subheader(post_title(post))
            st.markdown(product_details_html(post), unsafe_allow_html=True)

            owns_post = st.session_state.get("access_token") and post.get(
                "user_id"
            ) == current_user.get("id")
            if owns_post:
                danger_col, clear_col = st.columns(2)
                with danger_col:
                    if st.button("Delete", type="primary", width="stretch"):
                        delete_post(post_id)
                with clear_col:
                    if st.button("Close", width="stretch"):
                        st.session_state.selected_post_id = ""
                        st.session_state.current_view = "feed"
                        st.rerun()
            else:
                if st.button("Close", width="stretch"):
                    st.session_state.selected_post_id = ""
                    st.session_state.current_view = "feed"
                    st.rerun()

    with right:
        with st.container(border=True):
            title_col, sort_col = st.columns([2.4, 1], vertical_alignment="center")
            with title_col:
                st.markdown("#### Public comments")
            with sort_col:
                sort_order = st.selectbox(
                    "Sort",
                    ["Newest first", "Oldest first"],
                    key=f"comment_sort_{post_id}",
                    help="Sort comments by time",
                    label_visibility="visible",
                )
            created_comment = None
            author_hint = (
                f"Posting as {user_display_name(current_user)}"
                if st.session_state.get("access_token")
                else "Posting as Anonymous user. Anonymous comments cannot be edited or deleted."
            )
            st.caption(author_hint)
            with st.form(f"comment_form_{post_id}", clear_on_submit=True):
                content = st.text_area(
                    "Add a comment",
                    max_chars=500,
                    height=130,
                    placeholder="Share your thoughts...",
                )
                submitted = st.form_submit_button("➤", help="Post comment")
            if submitted:
                created_comment = create_comment(post_id, content)

            comments = fetch_comments(post_id)
            if sort_order == "Oldest first":
                comments = list(reversed(comments))
            if created_comment:
                comments = [
                    comment
                    for comment in comments
                    if comment.get("id") != created_comment.get("id")
                ]
                if sort_order == "Oldest first":
                    comments.append(created_comment)
                else:
                    comments.insert(0, created_comment)
                clear_read_cache()
            if not comments:
                st.caption("No comments yet.")
                return

            comment_area = st.container(height=520, border=False)
            with comment_area:
                for comment in comments:
                    like_count = int(comment.get("like_count") or 0)
                    dislike_count = int(comment.get("dislike_count") or 0)
                    can_manage = (
                        st.session_state.get("access_token")
                        and comment.get("user_id") == current_user.get("id")
                        and is_edit_window_open(comment.get("can_edit_until"))
                    )
                    can_delete_anonymous = (
                        st.session_state.get("access_token")
                        and comment.get("user_id") is None
                        and owns_post
                    )

                    with st.container(border=True):
                        header_col, delete_col = st.columns(
                            [6, 0.6], vertical_alignment="top"
                        )
                        with header_col:
                            st.markdown(
                                f"""
                                <div class="comment-author">{escape(comment.get("author_name", "User"))}</div>
                                <div class="media-sub">Commented on {format_date(comment.get("created_at"))}</div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with delete_col:
                            if (can_manage or can_delete_anonymous) and st.button(
                                " ",
                                key=f"delete_comment_{comment['id']}",
                                help="Delete comment",
                                icon=":material/delete:",
                                type="tertiary",
                                width="content",
                            ):
                                if delete_comment(comment["id"]):
                                    st.rerun()

                        st.markdown(
                            f'<div class="comment-body">{linkify_comment(comment.get("content", ""))}</div>',
                            unsafe_allow_html=True,
                        )

                        reaction = comment.get("user_reaction")
                        like_col, dislike_col, _ = st.columns([0.75, 0.75, 5.5])
                        with like_col:
                            if st.button(
                                str(like_count),
                                key=f"like_{comment['id']}",
                                help="Like comment",
                                icon=":material/thumb_up:",
                                type="primary" if reaction == "like" else "secondary",
                                width="content",
                            ):
                                if react_to_comment(comment["id"], "like"):
                                    st.rerun()
                        with dislike_col:
                            if st.button(
                                str(dislike_count),
                                key=f"dislike_{comment['id']}",
                                help="Dislike comment",
                                icon=":material/thumb_down:",
                                type="primary"
                                if reaction == "dislike"
                                else "secondary",
                                width="content",
                            ):
                                if react_to_comment(comment["id"], "dislike"):
                                    st.rerun()

                        if can_manage:
                            with st.form(f"edit_comment_{comment['id']}"):
                                edited = st.text_area(
                                    "Edit comment",
                                    value=comment.get("content") or "",
                                    max_chars=500,
                                    height=110,
                                )
                                save = st.form_submit_button(
                                    "Save",
                                    help="Save comment",
                                    icon=":material/check:",
                                    width="content",
                                )
                            if save and update_comment(comment["id"], edited):
                                st.rerun()


def main() -> None:
    init_state()
    handle_query_actions()
    inject_styles()

    render_sidebar()

    render_hero()
    st.write("")

    current_view = st.session_state.get("current_view", "feed")
    if current_view == "create":
        render_upload_panel()
        return

    if current_view == "my_reviews":
        render_my_reviews()
        return

    if current_view == "manage":
        if not st.session_state.get("selected_post_id"):
            st.session_state.current_view = "feed"
            st.rerun()
        render_selected_post()
        return

    with st.container(key="feed_page_shell"):
        posts = fetch_feed(limit=40)
        search, limit, media_filter, category_filter, country_filter = render_filters(
            posts
        )
        visible_posts = filter_posts(
            posts,
            media_filter,
            category_filter,
            country_filter,
            search=search,
            limit=limit,
        )
        render_metrics(visible_posts)
        st.write("")
        render_feed(visible_posts)


if __name__ == "__main__":
    main()
