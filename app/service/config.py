# app/service/config.py
import os

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    class Config:
        env_file = ".env"  # Specify the path to your .env file

# Instantiate the settings
settings = Settings()
