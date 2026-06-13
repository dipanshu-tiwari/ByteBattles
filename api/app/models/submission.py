from ..core.database import Base
from ..core.storage import storage_testcases, storage_submission_code
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .enums import Verdict, Language

class Submission(Base):
    __tablename__="submissions"

    id = Column(Integer, primary_key=True)

    language = Column(
        SQLEnum(Language),
        nullable=False,
        default=Language.C
    )

    code_object_key = Column(String, nullable=False, unique=True)
    submitted_at = Column(DateTime, server_default=func.now(), nullable=False)

    problem_id = Column(
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False
    )

    problem = relationship(
        "Problem",
        back_populates="submissions"
    )

    user_id = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="submissions"
    )

    verdict = Column(
        SQLEnum(Verdict),
        nullable=False,
        default=Verdict.PENDING
    )

    incorrect_testcase_key = Column(String, nullable=True)
    output = Column(Text, nullable=True)

    walltime_ms = Column(Integer, nullable=True)
    memory_kb = Column(Integer, nullable=True)

    @property
    def username(self):
        return self.user.username
    
    @property
    def incorrect_testcase(self):
        return storage_testcases.get_file(self.incorrect_testcase_key) if self.incorrect_testcase_key and storage_submission_code.file_exists(self.incorrect_testcase_key) else None
    
    @property
    def code(self):
        return storage_submission_code.get_file(self.code_object_key)