from fastapi import FastAPI

from app.routers.story import router as story_router
from app.routers.investigation import router as investigation_router
from app.routers.progress import router as progress_router
from app.routers.auth import router as auth_router
from app.routers.login import router as login_router


app = FastAPI(
    title="Shrek: Who Killed the King?",
    description="Interactive detective story API",
    version="1.0.0"
)


app.include_router(story_router)
app.include_router(investigation_router)
app.include_router(progress_router)
app.include_router(auth_router)
app.include_router(login_router)


@app.get("/")
def home():
    return {"message": "Shrek Detective API is running"}