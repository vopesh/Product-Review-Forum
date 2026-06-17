from dataclasses import dataclass

from imagekitio import ImageKit

from app.core.config import settings


DEFAULT_UPLOAD_FOLDER = "/post_uploads/"


@dataclass(frozen=True)
class ImageKitUpload:
    url: str
    file_id: str
    file_name: str


imagekit = ImageKit(private_key=settings.IMAGEKIT_PRIVATE_KEY)


def upload_media(
    *,
    content: bytes,
    filename: str,
    folder: str = DEFAULT_UPLOAD_FOLDER,
) -> ImageKitUpload:
    """Upload one image/video to ImageKit DAM and return DB-safe metadata."""
    upload_info = imagekit.files.upload(
        file=content,
        file_name=filename,
        folder=folder,
        use_unique_file_name=True,
    )

    if not upload_info.url or not upload_info.file_id:
        raise ValueError("ImageKit upload response did not include url or file_id")

    return ImageKitUpload(
        url=upload_info.url,
        file_id=upload_info.file_id,
        file_name=upload_info.name or filename,
    )


def delete_media(file_id: str) -> None:
    imagekit.files.delete(file_id)


def bulk_delete_media(file_ids: list[str]) -> None:
    imagekit.files.bulk.delete(file_ids=file_ids)
