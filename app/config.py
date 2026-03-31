from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, ClassVar, Tuple, Optional

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Animal Recognition API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Model settings
    MODEL_INPUT_SIZE: Tuple[int, int] = (224, 224)  # Width, Height
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: ClassVar[List[str]] = ["image/jpeg", "image/png", "image/webp"]
    
    # Database settings
    MONGO_URI: str = "mongodb://localhost:27017"
    
    # PostgreSQL settings (Added to fix validation error)
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None

    # Collection names
    ANIMALS: str = "animals"
    OWN_ANIMALS: str = "own_animals"
    USER: str = "users"
    MARKET_ANIMALS: str = "market_animals"
    MARKET: str = "marketplace"
    MACHINES: str = "machines"
    
    # Twilio settings
    ACCOUNT_SSID: Optional[str] = None
    AUTH_TOKEN: Optional[str] = None
    FROM_WHATSAPP_NUMBER: Optional[str] = None
    
    # JWT settings
    HASH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRY_MINUTES: int = 60
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore" # Safely ignore extra env vars instead of crashing
    )
        
settings = Settings()
