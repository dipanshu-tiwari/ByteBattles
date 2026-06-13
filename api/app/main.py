from fastapi import FastAPI

from .core.database import engine
from . import models
from .routes import auth, users, problems, submissions

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(problems.router)
app.include_router(submissions.router)