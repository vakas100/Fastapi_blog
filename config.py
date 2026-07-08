from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str = "sqlite+aiosqlite:///./blog.db"

    max_profile_image_size: int = 5 * 1024 * 1024 # 5MB

    posts_per_page: int = 10

    reset_token_expire_minutes: int = 60

    # Email configuration
    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:8000"



settings = Settings() #this is loaded from .env file
