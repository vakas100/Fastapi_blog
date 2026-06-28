from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse, UserCreate, UserResponse

from typing import Annotated

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get('/', response_class=HTMLResponse,include_in_schema=False)
@app.get('/posts', response_class=HTMLResponse,include_in_schema=False)   # both these routes returns same thing to hide these in docs we use include in schema false
def home(): 
    return f"<h1>Welcome to Fastapi Blog</h1>"

@app.get('/api/users/{user_id}', response_model=UserResponse)
def get_users(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.get('/api/users/{user_id}/posts', response_model=list[PostResponse])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts = result.scalars().all()
    
    if posts:
        return posts
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posts not found")


@app.get('/api/posts', response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

@app.get('/api/posts/{post_id}', response_model=PostResponse)
def getpost(post_id : int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id==post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.post(
        "/api/users",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):

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

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    )
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id==post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post
