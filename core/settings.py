import json
import os
import secrets

from typing import Any, ClassVar, Optional

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic.fields import FieldInfo, computed_field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class JsonConfigSettingsSource(PydanticBaseSettingsSource):

    json_secret: ClassVar[dict[str, Any]] = {}


    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        field_value = self.json_secret.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:  # noqa: ANN401
        return value

    def __call__(self) -> dict[str, Any]:  # noqa: D102
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(field,field_name)
            field_value = self.prepare_field_value(field_name, field, field_value, value_is_complex)
            if field_value is not None:
                d[field_key] = field_value

        return d


class Settings(BaseSettings):

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: Optional[str] = None
    SERVER_HOST: Optional[AnyHttpUrl] = None
    SERVER_ADDRESS: Optional[str] = None
    SERVER_PORT: int = int(os.getenv("PORT", 8000))  # Default 8000, but use PORT for Render
    BACKEND_CORS_ORIGINS: list[str] = []

    @classmethod
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: list[str]) -> list[str]:
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    try:
                        return json.loads(item)
                    except json.JSONDecodeError:
                        raise ValueError(v) from None
            return v

    FRONTEND_URL: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_POOL_SIZE: int = 50
    POSTGRES_MAX_OVERFLOW: int = 0

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Check for DATABASE_URL first (Railway, Render, etc.)
        if "DATABASE_URL" in os.environ:
            db_url = os.environ["DATABASE_URL"]
            # Convert postgresql:// to postgresql+psycopg:// for compatibility
            if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
            return db_url
        
        # Build database URI only if we have the required values
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            return ""
        
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                path=f"{self.POSTGRES_DB or ''}",
            )
        )

    # Cookie
    COOKIE_KEY: Optional[str] = None

    WATCH_FILES: bool = False
    LOG_LEVEL: str = "info"  # Logging level: critical, error, warning, info, debug, trace

    class Config:
        env_file = "local.env"
        case_sensitive = True
        extra = "allow"
        env_ignore_empty = True

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return JsonConfigSettingsSource(settings_cls), dotenv_settings

settings = Settings()
