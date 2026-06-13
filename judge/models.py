from api.app.models.problem import TestCase, Problem
from api.app.models.submission import Submission
from api.app.models.enums import Language, Verdict

FILENAME = {
    Language.C: "main.c",
    Language.CPP: "main.cpp",
    Language.PYTHON: "main.py"
}

IMAGE = {
    Language.C: "judge-gcc:latest",
    Language.CPP: "judge-gcc:latest",
    Language.PYTHON: "judge-python:latest",
}