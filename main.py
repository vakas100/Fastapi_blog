from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routers import posts, users


from contextlib import asynccontextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager  # used for table creation at startup and shutdown
async def lifespan(_app: FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
    #shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/media", StaticFiles(directory=BASE_DIR / "media", check_dir=False), name="media")

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.get('/', response_class=HTMLResponse,include_in_schema=False)
@app.get('/posts', response_class=HTMLResponse,include_in_schema=False)   # both these routes returns same thing to hide these in docs we use include in schema false
def home(): 
    return f"<h1>Welcome to Fastapi Blog</h1>"



