import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import cloudinary, cloudinary.uploader
from .. import models, schemas
from ..deps import get_current_user, rate_limit_me, require_admin
from ..cache import invalidate_user
from .. import crud
from ..database import get_db
from ..settings import settings

router = APIRouter(prefix="/users", tags=["users"])

def _ensure_cloudinary():
    """Перевіряє конфіг Cloudinary щоразу перед аплоудом (коментарі українською)."""
    # 1) Пробуємо URL
    cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL, secure=True)
    cfg = cloudinary.config()
    # 2) Якщо по URL не налаштовано — пробуємо окремі змінні
    if not (cfg.api_key and cfg.api_secret and cfg.cloud_name):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        cfg = cloudinary.config()
    if not (cfg.api_key and cfg.api_secret and cfg.cloud_name):
        raise HTTPException(
            status_code=503,
            detail="Cloudinary misconfigured: check CLOUDINARY_URL or CLOUDINARY_* vars",
        )
    return cfg

@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    # Ліміт на 5 запитів на хвилину
    rate_limit_me(current_user.id)
    return current_user

@router.post("/me/avatar", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_cloudinary()
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="contacts_api/avatars",
            public_id=str(current_user.id),
            overwrite=True,
            resource_type="image",
        )
    except Exception as e:
        # Узкий 502, чтобы отличать сетевые/SDK проблемы Cloudinary
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {e.__class__.__name__}") from e

    url = result.get("secure_url")
    if not url:
        raise HTTPException(status_code=500, detail="Upload failed")
    current_user.avatar_url = url
    db.commit()
    db.refresh(current_user)
    invalidate_user(current_user.id)
    return current_user

@router.post("/admin/default-avatar", status_code=status.HTTP_201_CREATED)
def set_default_avatar(url: str, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    """Адмін встановлює глобальний аватар за замовчуванням (використовується, якщо у користувача немає avatar_url)."""
    crud.meta_set(db, "default_avatar_url", url)
    return {"detail": "Default avatar updated", "url": url}

@router.get("/default-avatar")
def get_default_avatar(db: Session = Depends(get_db)):
    """Повертає поточний глобальний аватар за замовчуванням."""
    from ..settings import settings as s
    url = crud.meta_get(db, "default_avatar_url") or s.DEFAULT_AVATAR_URL
    return {"url": url}
