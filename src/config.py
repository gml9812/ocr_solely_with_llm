from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str
    allowed_file_types: dict = {"image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "application/pdf": [".pdf"]}
    max_file_size_mb: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8" 