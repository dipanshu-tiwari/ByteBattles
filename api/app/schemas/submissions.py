from pydantic import BaseModel
from datetime import datetime

from ..models.enums import Verdict, Language

class SubmissionCreate(BaseModel):
    problem_id: str
    code: str
    language: Language

class SubmissionResponse(BaseModel):
    id: int
    language: Language
    submitted_at: datetime
    problem_id: str
    username: str
    verdict: Verdict
    incorrect_testcase: str | None
    output: str | None
    walltime_ms: int | None
    memory_kb: int | None
    code: str

class SubmissionHeaderResponse(BaseModel):
    id: int
    submitted_at: datetime
    problem_id: str
    username: str
    verdict: Verdict
    walltime_ms: int | None
    memory_kb: int | None

    model_config = {
        "from_attributes": True
    }