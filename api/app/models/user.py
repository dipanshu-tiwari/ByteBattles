from ..core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .enums import UserType

class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, server_default="FALSE")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user_type = Column(
        SQLEnum(UserType),
        nullable=False,
        default=UserType.USER
    )

    submissions = relationship(
        "Submission",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # rating = Integer(default=0, nullable=False)
    # max_rating = Integer(default=0, nullable=False)