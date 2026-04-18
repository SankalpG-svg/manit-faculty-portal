import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal
from bson import ObjectId

# ── Nested models ──────────────────────────────────────────────
class Publication(BaseModel):
    title: str
    venue_type: str  # e.g., "Journal" or "Conference" (Added from notes)
    publisher: str
    year: int
    pdf_url: Optional[str] = None

class Experience(BaseModel):
    institution: str
    role: str
    start_year: int
    end_year: Optional[int] = None
    description: Optional[str] = None

class Certification(BaseModel):
    title: str
    issuing_body: str
    year: int
    certificate_url: Optional[str] = None

# ── Core Faculty models ────────────────────────────────────────
class FacultyBase(BaseModel):
    name: str
    email: EmailStr
    emp_id: Optional[str] = None  # Optional because pending users don't have one yet
    department: str
    designation: str
    profile_photo_url: Optional[str] = None
    status: Literal["pending", "unclaimed", "claimed"] = "pending"

    # ── NEW: Public Display Fields (From MANIT site) ──
    qualification: Optional[str] = None
    research_area: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

    # ── NEW: Personal Details (From Notes) ──
    dob: Optional[str] = None 

    # ── UPDATED: Professional Detail Lists ──
    subjects_current_sem: List[str] = []
    publications: List[Publication] = []
    experience: List[Experience] = []
    certifications: List[Certification] = []
    events_organized: List[str] = []
    foreign_visits: List[str] = []

class FacultyRegister(BaseModel):
    """Step 1: Faculty applies for an account (No emp_id or password yet)."""
    name: str
    email: EmailStr
    department: str
    designation: str

class FacultyApprove(BaseModel):
    """Step 2: Admin approves and assigns emp_id and strong password."""
    emp_id: str
    password: str

    @field_validator('password')
    @classmethod
    def strong_password(cls, v: str):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain a lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain a number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain a special character')
        return v

class FacultyInDB(FacultyBase):
    id: Optional[str] = Field(None, alias="_id")
    password_hash: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class FacultyResponse(FacultyBase):
    id: str
    class Config:
        populate_by_name = True

class FacultyUpdate(BaseModel):
    """Used for PATCH requests where any field can be updated independently."""
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    profile_photo_url: Optional[str] = None
    status: Optional[Literal["pending", "unclaimed", "claimed"]] = None
    
    # ── NEW: Public Fields ──
    qualification: Optional[str] = None
    research_area: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    
    # ── NEW: Personal Fields ──
    dob: Optional[str] = None 
    
    # ── UPDATED: Professional Detail Lists ──
    subjects_current_sem: Optional[List[str]] = None
    publications: Optional[List[Publication]] = None
    experience: Optional[List[Experience]] = None
    certifications: Optional[List[Certification]] = None
    events_organized: Optional[List[str]] = None
    foreign_visits: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "designation": "Associate Professor",
                "research_area": "Machine Learning, Game Theory",
                "profile_photo_url": "https://res.cloudinary.com/demo/image/upload/profile.jpg"
            }
        }