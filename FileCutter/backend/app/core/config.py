from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    confirmation_token_secret: str = "super_secret_confirmation_token_123"
    lm_studio_url: str = "http://localhost:1234/v1/chat/completions"
    downloads_path: str = "./downloads"

    class Config:
        env_file = ".env"

settings = Settings()
