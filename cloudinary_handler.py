# app/utils/cloudinary_handler.py
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
from config import settings

# ── Allowed types per upload category ─────────────────────────
PHOTO_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
PDF_MIME_TYPES   = {"application/pdf"}

FOLDER_PHOTOS = "faculty_portal/profile_photos"
FOLDER_PAPERS = "faculty_portal/research_papers"

MAX_PHOTO_BYTES = 5  * 1024 * 1024
MAX_PDF_BYTES   = 20 * 1024 * 1024

def _init_cloudinary():
    """Configure the SDK once, lazily."""
    # UPDATED: Using the 'portal_' names we set in config.py
    cloudinary.config(
        cloud_name=settings.portal_cloud_name,
        api_key=settings.portal_api_key,
        api_secret=settings.portal_api_secret,
        secure=True,
    )

async def _read_and_validate(file: UploadFile, allowed: set[str], max_bytes: int) -> bytes:
    """Read file bytes and validate content-type + size."""
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {sorted(allowed)}",
        )
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data)/1024/1024:.1f} MB). Max allowed: {max_bytes//1024//1024} MB",
        )
    return data

async def upload_profile_photo(file: UploadFile) -> dict:
    _init_cloudinary()
    data = await _read_and_validate(file, PHOTO_MIME_TYPES, MAX_PHOTO_BYTES)

    try:
        # Use a list for the transformation as expected by Cloudinary SDK
        result = cloudinary.uploader.upload(
            data,
            folder=FOLDER_PHOTOS,
            resource_type="image",
            transformation=[{"width": 400, "height": 400, "crop": "fill", "gravity": "face"}],
            overwrite=True,
        )
    except Exception as exc:
        # If this fails, the error message in Swagger will tell us why
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {exc}")

    return {"secure_url": result["secure_url"], "public_id": result["public_id"]}

async def upload_research_paper(file: UploadFile) -> dict:
    _init_cloudinary()
    data = await _read_and_validate(file, PDF_MIME_TYPES, MAX_PDF_BYTES)

    try:
        result = cloudinary.uploader.upload(
            data,
            folder=FOLDER_PAPERS,
            resource_type="raw",
            overwrite=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {exc}")

    return {"secure_url": result["secure_url"], "public_id": result["public_id"]}