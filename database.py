from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# ── FIXED IMPORT (No dot, no 'app.') ──
from config import settings

# Module-level client – created once, reused across requests
_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client

def get_db() -> AsyncIOMotorDatabase:
    return get_client()[settings.db_name]

# ── Collection helpers ────────────────────────────────────────

def faculty_collection():
    return get_db()["faculty"]

# ── Startup / shutdown hooks (plug into FastAPI lifespan) ─────

async def connect_db():
    """Call on app startup – verifies the connection is alive."""
    client = get_client()
    await client.admin.command("ping")
    print(f"[DB] Connected to MongoDB at {settings.mongo_uri}")

async def close_db():
    """Call on app shutdown."""
    global _client
    if _client:
        _client.close()
        _client = None
        print("[DB] MongoDB connection closed")