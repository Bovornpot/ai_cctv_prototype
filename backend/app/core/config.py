import os

class Settings:
    API_KEY = os.getenv("API_KEY", "nemo1234")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/master_database_filtered.sqlite")

settings = Settings()
