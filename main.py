from fastapi import FastAPI, status

app = FastAPI(
    title="CRUD API",
    version="0.1.0",
)


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    summary="Check service health",
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}