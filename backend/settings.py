from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TOKEN: str
    WHATSAPP_MODE: str
    PHONE_NUMBER_ID: str | None = None
    WHATSAPP_API_VERSION: str
    WHATSAPP_DRY_RUN: bool = True
    WHATSAPP_ACCESS_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Evita erros se houver variáveis a mais no ambiente
    )

settings = Settings()