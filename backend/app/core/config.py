import os
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKEND_ENV_FILE = os.path.join(_BACKEND_DIR, ".env")

class Settings(BaseSettings):
    APP_NAME: str = "EduResolve AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # MySQL Database Configuration (XAMPP MySQL)
    DATABASE_URL: Optional[str] = None
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "eduresolve_ai"
    
    # Dedicated MySQL Test Database
    MYSQL_TEST_DATABASE: str = "eduresolve_ai_test"
    
    # JWT Security
    JWT_SECRET_KEY: str = "super-secret-eduresolve-ai-jwt-key-change-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    DEFAULT_INSTITUTION_PASSWORD: str = "EduResolve@123"
    
    # CORS
    FRONTEND_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # File Storage (Private non-public directory)
    UPLOAD_DIR: str = os.path.join(_BACKEND_DIR, "private_uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # AI Feature Flags ("local", "rule_based", "openai", "none")
    AI_PROVIDER: str = "local"
    AI_API_KEY: Optional[str] = None
    
    # SMTP (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "notifications@eduresolve.ai"
    SMTP_USE_TLS: bool = True
    
    # Frontend Base URL
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Email Verification Settings
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS: int = 60
    
    # Notification & Outbox Settings
    NOTIFICATION_OUTBOX_MAX_RETRIES: int = 3
    NOTIFICATION_EMAIL_ENABLED: bool = True
    
    # SLA Scheduler Settings
    SLA_SCHEDULER_ENABLED: bool = True
    SLA_POLL_INTERVAL_SECONDS: int = 300
    SLA_WARNING_HOURS: int = 24
    AICTE_ALERT_WARNING_HOURS: int = 48
    AICTE_ALERT_DEDUP_HOURS: int = 24
    AICTE_TRANSFER_PENDING_WARNING_HOURS: int = 72
    
    # Rate Limiting & Security Safeguards
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_MAX_REQUESTS: int = 10
    RATE_LIMIT_REGISTER_MAX_REQUESTS: int = 5
    RATE_LIMIT_VERIFY_RESEND_MAX_REQUESTS: int = 3
    MAX_CONTENT_LENGTH_MB: int = 15
    
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("MYSQL_HOST")
    @classmethod
    def validate_mysql_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("MYSQL_HOST cannot be empty.")
        return v.strip()

    @field_validator("MYSQL_PORT")
    @classmethod
    def validate_mysql_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"MYSQL_PORT must be between 1 and 65535, got {v}.")
        return v

    @field_validator("MYSQL_USER")
    @classmethod
    def validate_mysql_user(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("MYSQL_USER cannot be empty.")
        return v.strip()

    @field_validator("MYSQL_DATABASE")
    @classmethod
    def validate_mysql_database(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("MYSQL_DATABASE cannot be empty.")
        return v.strip()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            url_lower = v.lower()
            if "sqlite" in url_lower:
                raise ValueError("SQLite is strictly prohibited. You must use MySQL via XAMPP (mysql+pymysql://).")
            if not (url_lower.startswith("mysql://") or url_lower.startswith("mysql+pymysql://")):
                raise ValueError("DATABASE_URL must start with 'mysql://' or 'mysql+pymysql://'.")
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        insecure_defaults = [
            "super-secret-eduresolve-ai-jwt-key-change-in-production-min-32-chars-long",
            "replace_with_a_secure_random_secret_min_32_chars",
            "secret",
            "changeme"
        ]
        if self.APP_ENV == "production":
            if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32 or self.JWT_SECRET_KEY in insecure_defaults:
                raise ValueError(
                    "Insecure default JWT_SECRET_KEY is prohibited in production. "
                    "A secure key with at least 32 characters must be configured in environment."
                )
        return self

    def get_database_uri(self) -> str:
        """
        Build and return the MySQL SQLAlchemy connection URI safely using SQLAlchemy URL utilities.
        SQLite is strictly prohibited.
        """
        if self.DATABASE_URL:
            parsed = make_url(self.DATABASE_URL)
            if parsed.get_backend_name() != "mysql":
                raise ValueError(
                    f"Invalid database dialect '{parsed.drivername}'. Only MySQL connections (mysql+pymysql) are permitted."
                )
            if parsed.drivername == "mysql":
                parsed = parsed.set(drivername="mysql+pymysql")
            return parsed.render_as_string(hide_password=False)

        url = URL.create(
            drivername="mysql+pymysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD if self.MYSQL_PASSWORD else None,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            database=self.MYSQL_DATABASE,
            query={"charset": "utf8mb4"}
        )
        return url.render_as_string(hide_password=False)

    def get_safe_database_uri(self) -> str:
        """
        Return the MySQL SQLAlchemy connection URI with credentials safely masked for logging.
        Never exposes the password.
        """
        try:
            parsed = make_url(self.get_database_uri())
            return parsed.render_as_string(hide_password=True)
        except Exception:
            return f"mysql+pymysql://{self.MYSQL_USER}:***@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    def get_test_database_uri(self) -> str:
        """
        Return dedicated test schema connection URL on XAMPP MySQL server.
        """
        url = URL.create(
            drivername="mysql+pymysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD if self.MYSQL_PASSWORD else None,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            database=self.MYSQL_TEST_DATABASE,
            query={"charset": "utf8mb4"}
        )
        return url.render_as_string(hide_password=False)

settings = Settings()
