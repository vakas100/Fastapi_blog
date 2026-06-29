from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse, PostUpdate, UserCreate, UserResponse, UserUpdate

from typing import Annotated
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
    #shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get('/', response_class=HTMLResponse,include_in_schema=False)
@app.get('/posts', response_class=HTMLResponse,include_in_schema=False)   # both these routes returns same thing to hide these in docs we use include in schema false
def home(): 
    return f"<h1>Welcome to Fastapi Blog</h1>"

@app.get('/api/users/{user_id}', response_model=UserResponse)
async def get_users(user_id: int,
                    db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User)
                              .where(models.User.id==user_id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.post(
        "/api/users",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="username already exists",)
    
    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email already exists",)

    new_user = models.User(
        username= user.username,
        email= user.email,
    )

    db.add(new_user)   # it doesn't require await because it is not an i/o bound task
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get('/api/users/{user_id}/posts', response_model=list[PostResponse])
async def get_user_posts(user_id: int,
                        db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(select(models.Post)
                              .options(selectinload(models.Post.author)) # this statement is used to load author object of Post whenever it is referred
                              .where(models.Post.user_id==user_id))
    posts = result.scalars().all()
    
    if posts:
        return posts
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posts not found")


@app.patch('/api/users/{user_id}', response_model=UserResponse)
async def update_user_full(user_id: int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(select(models.User).where(models.User.username==user_update.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(select(models.User).where(models.User.email==user_update.email))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file
    
    await db.commit()
    await db.refresh(user)
    return user

@app.delete('/api/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()


@app.get('/api/posts', response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    )
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.id==post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["Author"])

    return new_post

@app.get('/api/posts/{post_id}', response_model=PostResponse)
async def get_post_using_postid(post_id : int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = db.execute(select(models.Post)
                        .options(selectinload(models.Post.author))
                        .where(models.Post.id==post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.put('/api/posts/{post_id}', response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != post_data.user_id:
        result = await db.execute(select(models.User).where(models.User.id==post_data.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, attribute_names=["Author"])

    return post

@app.patch('/api/posts/{post_id}', response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = db.execute(select(models.Post)
                        .options(selectinload(models.Post.author))
                        .where(models.Post.id==post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # important *
    update_data = post_data.model_dump(exclude_unset=True) # -> dict
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["Author"])
    return post

@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id : int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post)
                              .options(selectinload(models.Post.author))
                              .where(models.Post.id==post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    await db.delete(post)
    await db.commit()




