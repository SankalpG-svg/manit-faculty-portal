# ─────────────────────────────────────────────────────────────
# backend/config.py – Robust Configuration Loader
# ─────────────────────────────────────────────────────────────
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# This finds the absolute path to your 'backend' folder
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # --- Database Settings ---
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "faculty_portal"
    
    # --- Auth Settings ---
    secret_key: str 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 

    # --- Cloudinary Settings ---
    portal_cloud_name: str
    portal_api_key: str
    portal_api_secret: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding='utf-8',
        extra="ignore"
    )

# Create the settings instance
settings = Settings()

# 🧪 Keeping the DEBUG PRINT is fine for now to verify the .env load
print("--- Configuration Status ---")
print(f"Loaded Cloud Name: {settings.portal_cloud_name}")
print("----------------------------")