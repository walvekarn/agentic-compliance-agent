from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


