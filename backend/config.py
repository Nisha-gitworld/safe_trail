from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/safetrail"
    MONGO_URI: str = "mongodb://localhost:27017/safetrail"
    REDIS_URL: str = "redis://localhost:6379"

    # Twilio
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_FROM: str = ""
    EMERGENCY_CONTACT_NUMBER: str = ""

    # Firebase
    FIREBASE_SERVICE_ACCOUNT: str = "./firebase-service-account.json"
    CITY_CODE: str = "MUM"

    # Blockchain
    POLYGON_RPC_URL: str = ""
    CONTRACT_ADDRESS: str = ""

    # AI
    OPENAI_API_KEY: str = ""

    # Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # Mock APIs
    POLICE_API_URL: str = "http://localhost:9001"
    HOSPITAL_API_URL: str = "http://localhost:9002"

    class Config:
        env_file = ".env"


settings = Settings()
