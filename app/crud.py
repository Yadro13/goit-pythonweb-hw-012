from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from . import models, schemas
from .security import hash_password, verify_password


def _payload_from(data):
    # Універсальний перетворювач у dict (укр. коментар)
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, dict):
        return data
    try:
        # берем только известные поля, чтобы не хватать лишнего
        fields = ["first_name", "last_name", "email", "phone", "birthday", "extra"]
        return {k: getattr(data, k) for k in fields if hasattr(data, k)}
    except Exception:
        return data.__dict__

# --- Users ---
def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    exists = db.scalar(select(func.count()).select_from(models.User).where(models.User.email == data.email))
    if exists:
        raise ValueError("User with this email already exists")
    user = models.User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = db.scalar(select(models.User).where(models.User.email == email))
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# --- Contacts (scoped by owner) ---
def create_contact(db: Session, owner_id: int, data: schemas.ContactCreate) -> models.Contact:
    obj = models.Contact(**_payload_from(data), owner_id=owner_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_contact(db: Session, owner_id: int, contact_id: int) -> Optional[models.Contact]:
    return db.scalar(select(models.Contact).where(models.Contact.id == contact_id, models.Contact.owner_id == owner_id))

def list_contacts(db: Session, owner_id: int, skip: int = 0, limit: int = 100,
                  first_name: Optional[str] = None,
                  last_name: Optional[str] = None,
                  email: Optional[str] = None) -> List[models.Contact]:
    stmt = select(models.Contact).where(models.Contact.owner_id == owner_id)
    conditions = []
    if first_name:
        conditions.append(models.Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        conditions.append(models.Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        conditions.append(models.Contact.email.ilike(f"%{email}%"))
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.offset(skip).limit(min(limit, 1000))
    return list(db.scalars(stmt).all())

def update_contact(db: Session, owner_id: int, contact_id: int, data: schemas.ContactUpdate) -> Optional[models.Contact]:
    obj = get_contact(db, owner_id, contact_id)
    if not obj:
        return None
    payload = _payload_from(data)
    for k, v in payload.items():
        if v is not None and hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete_contact(db: Session, owner_id: int, contact_id: int) -> bool:
    obj = get_contact(db, owner_id, contact_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def upcoming_birthdays(db: Session, owner_id: int, days: int = 7) -> List[models.Contact]:
    today = date.today()
    end = today + timedelta(days=days)
    contacts = list(db.scalars(select(models.Contact).where(models.Contact.owner_id == owner_id)).all())
    result = []
    for c in contacts:
        b = c.birthday
        try:
            next_bd = b.replace(year=today.year)
        except ValueError:
            next_bd = date(today.year, 2, 28)  # 29 Feb → 28 Feb у невисокосні роки
        if next_bd < today:
            try:
                next_bd = b.replace(year=today.year + 1)
            except ValueError:
                next_bd = date(today.year + 1, 2, 28)
        if today <= next_bd <= end:
            result.append(c)
    return result


def set_password(db: Session, user: models.User, new_password: str) -> models.User:
    """Оновлює хеш пароля користувача."""
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user

def set_user_role(db: Session, user_id: int, role: str) -> Optional[models.User]:
    """Адмін змінює роль користувача."""
    obj = db.get(models.User, user_id)
    if not obj:
        return None
    obj.role = role
    db.commit()
    db.refresh(obj)
    return obj

def meta_get(db: Session, key: str) -> Optional[str]:
    m = db.get(models.AppMeta, key)
    return m.value if m else None

def meta_set(db: Session, key: str, value: str | None) -> None:
    m = db.get(models.AppMeta, key)
    if m:
        m.value = value
    else:
        m = models.AppMeta(key=key, value=value)
        db.add(m)
    db.commit()
