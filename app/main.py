from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException

from .database import engine
from .routers import blog
from .templating import templates

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(blog.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request,
            "errors/404.html",
            {"detail": exc.detail},
            status_code=404
        )
    return templates.TemplateResponse(
        request,
        "errors/error.html",
        {"status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )