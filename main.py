from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine
from exception import AppError
from routers.organizations import router as organizations_router
from routers.users import router as users_router

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    yield

    await engine.dispose()

app = FastAPI(
    title="CRUD API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ],
    allow_headers=[
        "Content-Type",
    ],
    expose_headers=[
        "Location",
        "X-Process-Time",
    ],
)

@app.middleware("http")
async def add_process_time_header(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = perf_counter()

    response = await call_next(request)

    process_time = perf_counter() - started_at
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

@app.exception_handler(AppError)
async def app_error_handler(
    _request: Request,
    exc: AppError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )

@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    summary="Check service health",
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(organizations_router)
app.include_router(users_router)