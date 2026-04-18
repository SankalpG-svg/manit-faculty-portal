from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload import router as upload_router

# ── FIXED IMPORTS ──
from database import connect_db, close_db
from faculty import router as faculty_router
from auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await connect_db()
    yield
    # Shutdown logic
    await close_db()

app = FastAPI(
    title="Faculty Portal API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS CONFIGURATION ──
# Added 127.0.0.1 to cover all local development bases
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTERS ──
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(auth_router,    prefix="/api/auth",    tags=["Auth"])
app.include_router(faculty_router, prefix="/api/faculty", tags=["Faculty"])

@app.get("/health")
async def health():
    return {"status": "ok"}