import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TG_API_ID = os.getenv("TG_API_ID")
    TG_API_HASH = os.getenv("TG_API_HASH")

    # Database
    DB_USER = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")  # Default to 127.0.0.1 for IPv4
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "telehealth")

    @property
    def DB_CONNECTION_STR(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Config()
