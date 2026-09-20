from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_PROJECT_ID: str = ""

    # Where Google sends the browser back after consent. Leave empty to derive
    # it from HOST/PORT; the value must match an Authorized redirect URI on the
    # OAuth client in Google Cloud Console.
    OAUTH_REDIRECT_URI: str = ""

    DATABASE_URL: str = "sqlite:///./data/classroom.db"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
