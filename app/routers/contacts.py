from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..deps import require_verified
from .. import models

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db), user: models.User = Depends(require_verified)):
    return crud.create_contact(db, owner_id=user.id, data=payload)

@router.get("", response_model=List[schemas.ContactOut])
def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_verified),
):
    return crud.list_contacts(db, owner_id=user.id, skip=skip, limit=limit, first_name=first_name, last_name=last_name, email=email)

@router.get("/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_verified)):
    obj = crud.get_contact(db, owner_id=user.id, contact_id=contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return obj

@router.put("/{contact_id}", response_model=schemas.ContactOut)
def update_contact(contact_id: int, payload: schemas.ContactUpdate, db: Session = Depends(get_db), user: models.User = Depends(require_verified)):
    obj = crud.update_contact(db, owner_id=user.id, contact_id=contact_id, data=payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return obj

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_verified)):
    ok = crud.delete_contact(db, owner_id=user.id, contact_id=contact_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Contact not found")
    return None

@router.get("/birthdays/upcoming", response_model=List[schemas.ContactOut])
def birthdays_upcoming(days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db), user: models.User = Depends(require_verified)):
    return crud.upcoming_birthdays(db, owner_id=user.id, days=days)
