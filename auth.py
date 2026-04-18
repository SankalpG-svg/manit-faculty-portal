from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from database import faculty_collection
from security import verify_password, create_access_token, hash_password 

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────

class ClaimAccountRequest(BaseModel):
    emp_id: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ── POST /auth/claim-account ─────────────────────────────────────────

@router.post("/claim-account", status_code=status.HTTP_200_OK)
async def claim_account(payload: ClaimAccountRequest):
    col = faculty_collection()
    faculty = await col.find_one({"emp_id": payload.emp_id})

    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found.")
    if faculty.get("status") == "claimed":
        raise HTTPException(status_code=400, detail="Account already claimed.")
    if faculty.get("status") != "unclaimed":
        raise HTTPException(status_code=400, detail="Account is not yet approved by Admin.")

    hashed = hash_password(payload.new_password)

    await col.update_one(
        {"emp_id": payload.emp_id},
        {"$set": {
            "password_hash": hashed,
            "status": "claimed",
            "failed_login_attempts": 0,
            "locked_until": None
        }}
    )
    return {"message": "Account successfully claimed. You can now log in."}


# ── POST /auth/login ─────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    col = faculty_collection()
    
    # Swagger/OAuth2 uses 'username' field for the ID
    faculty = await col.find_one({"emp_id": form_data.username})

    if not faculty:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if faculty.get("status") == "pending":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is pending admin approval")

    # Check if account is locked
    locked_until = faculty.get("locked_until")
    if locked_until:
        if locked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account locked. Try again in 15 minutes.")

    # Verify Password
    if not faculty.get("password_hash") or not verify_password(form_data.password, faculty["password_hash"]):
        attempts = faculty.get("failed_login_attempts", 0) + 1
        updates = {"failed_login_attempts": attempts}
        
        if attempts >= 5:
            updates["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
            
        await col.update_one({"_id": faculty["_id"]}, {"$set": updates})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # ── SUCCESS LOGIC ──
    updates = {"failed_login_attempts": 0, "locked_until": None}
    
    # Auto-claim if they were just approved
    if faculty.get("status") == "unclaimed":
        updates["status"] = "claimed"
        
    await col.update_one({"_id": faculty["_id"]}, {"$set": updates})

    # ── ROLE DETERMINATION ──
    # If the Employee ID is ADMIN01, they get the 'admin' role
    is_admin = faculty["emp_id"] == "ADMIN01"
    
    token_data = {
        "sub": faculty["emp_id"],
        "role": "admin" if is_admin else "faculty",
        "email": faculty["email"]
    }

    # Generate the token with the role included
    token = create_access_token(data=token_data)
    
    return TokenResponse(access_token=token)