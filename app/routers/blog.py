from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def post_list(
    request: Request, 
    db: Session = Depends(get_db)
    ):
    posts = db.query(Post).all()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "posts": posts}
        )


@router.get("/{category_slug}/")
def get_category(
    category_slug: str,
    request: Request,
    db: Session = Depends(get_db)
    ):
    
    category = db.query(Category).filter_by(slug=category_slug).first()

    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada o inexistente")

    return templates.TemplateResponse(
        "category.html" , 
        {"request":request, "posts": category.posts}
        )


@router.get("/{category_slug}/{post_slug}/")
def get_post(
    category_slug: str,
    post_slug: str,
    request: Request,
    db: Session = Depends(get_db)
    ):

    post = db.query(Post).join(Category).filter(
        and_(
            Category.slug == category_slug,
            Post.slug == post_slug
            )
    ).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado o categoria no encontrada")

    return templates.TemplateResponse(
        "post.html", 
        {"request":request, "post":post}
        )