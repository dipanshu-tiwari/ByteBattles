from pydantic import BaseModel
from typing import Dict, List
from ..models.enums import Difficulty

class ProblemResponse(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    tags: List[str]
    accepted_submissions: int

class ProblemDetailResponse(ProblemResponse):
    description: str
    constraints: List[str]
    input_desc: str
    output_desc: str
    sample_io: Dict[str, str]
    explanation: str | None

    memory_limit_mb: int
    time_limit_sec: int

    source: str | None
    editorial: str | None
    visibility: bool

class ProblemArrayDataValidator(BaseModel):
    tags: List[str]
    constraints: List[str]
    sample_io: Dict[str, str]

class TagCreate(BaseModel):
    name: str
    slug: str

class ProblemCreateResponse(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    tags: List[str]
    testcases: int