from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, status


async def get_bearer_token(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    return authorization.split(" ", 1)[1]
