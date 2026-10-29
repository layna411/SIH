from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.core.config import settings

# Configure Argon2 password hashing through pwdlib
password_hasher = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """Hash password using Argon2id through pwdlib."""
    return password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2 hash through pwdlib."""
    if not plain_password or not hashed_password:
        return False
    try:
        return password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False

def create_access_token(
    subject: Union[str, Any],
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token with explicit expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    if extra_claims:
        to_encode.update(extra_claims)
        
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token with explicit signature and expiry checks.
    Returns decoded payload or None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.PyJWTError):
        return None

