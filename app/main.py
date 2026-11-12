from fastapi import FastAPI
from app.routers.story import router as story_router

app = FastAPI(
    title="Shrek: Who Killed the King?",
    description="Interactive detective story API",
    version="1.0.0"
)

app.include_router(story_router)


@app.get("/")
def home():
    return {"message": "Shrek Detective API is running"}
