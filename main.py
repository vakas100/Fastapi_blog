from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

import models
from config import settings
from database import Base, engine, get_db
from routers import posts, users


from typing import Annotated
from contextlib import asynccontextmanager



@asynccontextmanager  # used for table creation at startup and shutdown
async def lifespan(_app: FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
    #shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.get('/', response_class=HTMLResponse,include_in_schema=False)
@app.get('/posts', response_class=HTMLResponse,include_in_schema=False)   # both these routes returns same thing to hide these in docs we use include in schema false
def home(): 
    return f"<h1>Welcome to Fastapi Blog</h1>"






