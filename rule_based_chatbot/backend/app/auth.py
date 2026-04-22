from itsdangerous import BadSignature, URLSafeSerializer
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminUser


pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except UnknownHashError:
        return False


def ensure_admin_user(db: Session, username: str, password: str) -> None:
    existing = db.scalar(select(AdminUser).where(AdminUser.username == username))
    if existing:
        return
    db.add(AdminUser(username=username, password_hash=hash_password(password)))
    db.commit()


def authenticate_admin(db: Session, username: str, password: str) -> AdminUser | None:
    admin = db.scalar(select(AdminUser).where(AdminUser.username == username))
    if not admin:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin


def create_session_token(secret_key: str, username: str) -> str:
    serializer = URLSafeSerializer(secret_key=secret_key, salt="admin-session")
    return serializer.dumps({"username": username})


def parse_session_token(secret_key: str, token: str) -> str | None:
    serializer = URLSafeSerializer(secret_key=secret_key, salt="admin-session")
    try:
        data = serializer.loads(token)
    except BadSignature:
        return None
    return data.get("username")
