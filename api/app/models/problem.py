from ..core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .enums import Difficulty

class Category(Base):
    __tablename__="categories"

    name = Column(String, nullable=False)
    slug = Column(String, primary_key=True)

    problems = relationship(
        "Problem",
        secondary="tags",
        back_populates="tags"
    )

class Problem(Base):
    __tablename__="problems"

    id = Column(String(6), primary_key=True, index=True)
    
    title = Column(String, nullable=False)
    difficulty = Column(
        SQLEnum(Difficulty),
        nullable=False,
        default=Difficulty.EASY
    )
    
    description = Column(Text, nullable=False)
    constraints = Column(JSON, nullable=False)
    input_desc = Column(Text, nullable=False)
    output_desc = Column(Text, nullable=False)
    sample_io = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    memory_limit_mb = Column(Integer, nullable=False)
    time_limit_sec = Column(Integer, nullable=False)

    tags = relationship(
        "Category",
        secondary="tags",
        back_populates="problems"
    )

    testcases = relationship(
        "TestCase",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

    visibility = Column(Boolean, server_default="FALSE")

    source = Column(String, nullable=True)

    accepted_submissions = Column(Integer, server_default="0")
    total_submissions = Column(Integer, server_default="0")

    editorial = Column(Text, nullable=True)

    submissions = relationship(
        "Submission",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

class TestCase(Base):
    __tablename__="testcases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    input_key = Column(String, nullable=False)
    output_key = Column(String, nullable=False)

    problem = relationship("Problem", back_populates="testcases")

class Tag(Base):
    __tablename__="tags"

    id = Column(ForeignKey("problems.id"), primary_key=True)
    slug = Column(ForeignKey("categories.slug"), primary_key=True)