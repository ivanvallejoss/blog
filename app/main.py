from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.routers import blog

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(blog.router)
app.mount("/static", StaticFiles(directory="static"), name="static")