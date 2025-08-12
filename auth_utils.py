# auth_utils.py
from passlib.context import CryptContext
from jose import jwt
import time
from typing import Optional

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = "change_this_to_a_long_random_secret"  # change en prod
JWT_ALG = "HS256"
JWT_EXP_SECONDS = 60 * 60 * 24 * 7  # 7 jours

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict, expires_in: Optional[int] = None) -> str:
    to_encode = data.copy()
    exp = int(time.time()) + (expires_in or JWT_EXP_SECONDS)
    to_encode.update({"exp": exp})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
