from datetime import date
from sqlalchemy.orm import Session
from app import crud

def test_user_crud_and_roles():
    from app.database import SessionLocal
    db: Session = SessionLocal()
    u = crud.create_user(db, type("obj", (), {"email":"c1@example.com","password":"password123"}))
    assert u.email == "c1@example.com"
    try:
        crud.create_user(db, type("obj", (), {"email":"c1@example.com","password":"x"}))
        assert False
    except ValueError:
        pass
    assert crud.authenticate_user(db, "c1@example.com", "password123")
    assert crud.authenticate_user(db, "c1@example.com", "bad") is None
    ur = crud.set_user_role(db, u.id, "admin")
    assert ur and ur.role == "admin"
    crud.meta_set(db, "default_avatar_url", "http://example.com/x.png")
    assert crud.meta_get(db, "default_avatar_url") == "http://example.com/x.png"
    db.close()

def test_contacts_crud_filters():
    from app.database import SessionLocal
    db: Session = SessionLocal()
    owner = crud.create_user(db, type("obj", (), {"email":"c2@example.com","password":"password123"}))
    # pass a simple object instead of pydantic; crud should handle it
    data1 = type("obj", (), {
        "first_name":"John","last_name":"Smith","email":"john@x.com","phone":"12345","birthday":date(1990,5,10),"extra":None
    })()
    data2 = {"first_name":"Jane","last_name":"Doe","email":"jane@x.com","phone":"99999","birthday":date(1988,12,31),"extra":"vip"}
    c1 = crud.create_contact(db, owner.id, data1)
    c2 = crud.create_contact(db, owner.id, data2)
    assert len(crud.list_contacts(db, owner.id)) == 2
    assert len(crud.list_contacts(db, owner.id, first_name="Joh")) == 1
    assert len(crud.list_contacts(db, owner.id, last_name="oe")) == 1
    assert len(crud.list_contacts(db, owner.id, email="@x.com")) == 2
    upd = crud.update_contact(db, owner.id, c1.id, type("obj", (), {"model_dump": lambda self, **kw: {"phone":"00000"}})())
    assert upd.phone == "00000"
    got = crud.get_contact(db, owner.id, c2.id)
    assert got.email == "jane@x.com"
    assert crud.delete_contact(db, owner.id, c2.id) is True
    assert crud.get_contact(db, owner.id, c2.id) is None
    ups = crud.upcoming_birthdays(db, owner.id, days=365)
    assert any(x.id == c1.id for x in ups)
    db.close()
