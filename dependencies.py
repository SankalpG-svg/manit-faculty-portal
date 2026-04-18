from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import faculty_collection
from security import decode_access_token

# This tells FastAPI where your login route is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decode the token (This uses your secret key)
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    # 2. Get the employee ID and ROLE from the token payload
    emp_id: str = payload.get("sub")
    user_role: str = payload.get("role")  # 👈 THIS IS THE MISSING PIECE
    
    if not emp_id:
        raise credentials_exception
        
    # 3. Verify the user actually exists in MongoDB
    col = faculty_collection()
    faculty = await col.find_one({"emp_id": emp_id})
    if faculty is None:
        raise credentials_exception
        
    # 🚀 4. ATTACH THE ROLE TO THE OBJECT
    # Even if MongoDB doesn't have a 'role' field, the token does!
    # This allows faculty.py to see if role == "admin"
    faculty["role"] = user_role 
    
    return faculty