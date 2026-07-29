from typing import Annotated

from fastapi import Cookie, Depends, Query, Response
from pydantic import BaseModel


class PaginationParams(BaseModel):
    limit: int
    offset: int


async def get_pagination(
    response: Response,
    limit: Annotated[
        int | None,
        Query(ge=1, le=100),
    ] = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    page_size: Annotated[
        int | None,
        Cookie(ge=1, le=100),
    ] = None,
) -> PaginationParams:
    if limit is not None:
        effective_limit = limit

        response.set_cookie(
            key="page_size",
            value=str(limit),
            max_age=60 * 60 * 24 * 30,
            path="/users",
            httponly=True,
            secure=False,
            samesite="lax",
        )
    elif page_size is not None:
        effective_limit = page_size
    else:
        effective_limit = 20

    return PaginationParams(
        limit=effective_limit,
        offset=offset,
    )


PaginationDep = Annotated[
    PaginationParams,
    Depends(get_pagination),
]