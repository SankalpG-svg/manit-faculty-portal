from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import List

from database import faculty_collection
from models import FacultyRegister, FacultyApprove, FacultyResponse, FacultyUpdate
from security import hash_password
from dependencies import get_current_user

router = APIRouter()

def _serialize(doc: dict) -> dict:
    """Helper to convert MongoDB _id to string id"""
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

# ── 1. Self Registration (Pending Status) ─────────────────────
@router.post("/register", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
async def register_faculty(payload: FacultyRegister):
    col = faculty_collection()
    if await col.find_one({"email": payload.email}):
        raise HTTPException(400, "Email already exists")

    doc = payload.model_dump()
    doc["status"] = "pending"
    doc["emp_id"] = None
    doc["password_hash"] = None
    doc["failed_login_attempts"] = 0
    doc["locked_until"] = None
    doc["publications"] = []
    doc["experience"] = []
    doc["certifications"] = []

    result = await col.insert_one(doc)
    created = await col.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(status_code=500, detail="Failed to create faculty record")
    return _serialize(created)

# ── 2. Admin Approval ─────────────────────────────────────────
@router.post("/{faculty_id}/approve", response_model=FacultyResponse)
async def approve_faculty(faculty_id: str, payload: FacultyApprove):
    col = faculty_collection()
    
    if await col.find_one({"emp_id": payload.emp_id}):
        raise HTTPException(400, "Employee ID already in use")

    faculty = await col.find_one({"_id": ObjectId(faculty_id)})
    if not faculty:
        raise HTTPException(404, "Faculty not found")
    if faculty.get("status") != "pending":
        raise HTTPException(400, "Faculty is already approved or claimed")

    update_data = {
        "emp_id": payload.emp_id,
        "password_hash": hash_password(payload.password),
        "status": "unclaimed"
    }

    result = await col.find_one_and_update(
        {"_id": ObjectId(faculty_id)},
        {"$set": update_data},
        return_document=True,
    )
    return _serialize(result)

# ── 3. List all (PUBLIC VIEW - Filters out 'pending') ─────────
@router.get("/", response_model=List[FacultyResponse])
async def list_faculty(skip: int = 0, limit: int = 50):
    col = faculty_collection()
    
    # Ensures public visitors only see verified members
    query = {"status": {"$ne": "pending"}}
    
    cursor = col.find(query, {"password_hash": 0}).skip(skip).limit(limit)
    return [_serialize(doc) async for doc in cursor]

# ── 3.5 Admin List (PRIVATE VIEW - Shows everyone) ────────────
@router.get("/admin/all", response_model=List[FacultyResponse])
async def get_admin_faculty_list(current_user: dict = Depends(get_current_user)):
    # Verification: Only users with the 'admin' role can see pending requests
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have administrative privileges."
        )
        
    col = faculty_collection()
    # Admin sees everything (pending, claimed, unclaimed)
    cursor = col.find({}, {"password_hash": 0})
    return [_serialize(doc) async for doc in cursor]

# ── 4. The /me Route ──────────────────────────────────────────
@router.patch("/me")
async def update_my_profile(
    payload: dict, 
    current_user: dict = Depends(get_current_user)
):
    col = faculty_collection()
    
    forbidden_fields = ["_id", "emp_id", "email", "password_hash", "role", "status"]
    update_data = {k: v for k, v in payload.items() if k not in forbidden_fields}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = await col.update_one(
        {"emp_id": current_user["emp_id"]}, 
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {"message": "Profile updated successfully"}

# ── 5. Get one ────────────────────────────────────────────────
@router.get("/{faculty_id}", response_model=FacultyResponse)
async def get_faculty(faculty_id: str):
    col = faculty_collection()
    doc = await col.find_one({"_id": ObjectId(faculty_id)}, {"password_hash": 0})
    if not doc:
        raise HTTPException(404, "Faculty not found")
    return _serialize(doc)

# ── 6. Update (Specific Faculty by ID) ────────────────────────
@router.patch("/{faculty_id}", response_model=FacultyResponse)
async def update_faculty(
    faculty_id: str, 
    payload: FacultyUpdate,
    current_user: dict = Depends(get_current_user)
):
    col = faculty_collection()
    
    if str(current_user.get("_id")) != faculty_id:
        raise HTTPException(status_code=403, detail="You can only edit your own profile")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(400, "No fields provided to update")

    result = await col.find_one_and_update(
        {"_id": ObjectId(faculty_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Faculty not found")
    return _serialize(result)

# ── 7. Delete ─────────────────────────────────────────────────
@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(faculty_id: str):
    col = faculty_collection()
    result = await col.delete_one({"_id": ObjectId(faculty_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Faculty not found")