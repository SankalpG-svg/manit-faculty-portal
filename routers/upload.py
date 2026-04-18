from fastapi import APIRouter, UploadFile, File, Query
from cloudinary_handler import upload_profile_photo, upload_research_paper
from pydantic import BaseModel

router = APIRouter()

class UploadResponse(BaseModel):
    # 1. Changed to 'file_url' so React can read it properly
    file_url: str 
    public_id: str
    message: str

# 2. Changed route to match what React is calling
@router.post(
    "/upload-profile-image", 
    response_model=UploadResponse,
    summary="Upload a profile photo or research paper PDF",
)
async def upload_file(
    file: UploadFile = File(..., description="Image (JPEG/PNG/WEBP) or PDF"),
    # 3. Added a default value ("profile_photo") so React doesn't crash if it forgets to send this!
    upload_type: str = Query(
        "profile_photo", 
        enum=["profile_photo", "research_paper"],
        description="What kind of file this is",
    ),
):
    """
    Upload a file to Cloudinary.
    """
    if upload_type == "profile_photo":
        # Using your custom handler!
        result = await upload_profile_photo(file)
        msg = "Profile photo uploaded successfully"
    else:
        result = await upload_research_paper(file)
        msg = "Research paper uploaded successfully"

    return UploadResponse(
        file_url=result["secure_url"], # Mapping Cloudinary's secure_url to file_url for React
        public_id=result["public_id"],
        message=msg,
    )