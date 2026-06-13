from dataclasses import dataclass, field
from typing import Any, Optional
from ..models import Verdict

@dataclass
class CompileResult:
    ok: bool
    output: str = ""
    exit_code: int = 0

@dataclass
class RunResult:
    ok: bool
    verdict: str
    output: str = ""
    exit_code: int = 0
    runtime_ms: int | None = None
    memory_kb: int | None = None

@dataclass
class SubmissionResult:
    submission_id: int
    verdict: Verdict
    output: str | None = None
    incorrect_testcase_idx: int | None = 0
    incorrect_testcase_key: str | None = None
    runtime_ms: int = None
    memory_kb: int = None