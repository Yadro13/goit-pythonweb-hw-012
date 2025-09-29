import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine
from .models import Base
from .routers import contacts, auth, users
from .settings import settings

log = logging.getLogger("contacts_api")

app = FastAPI(
    title="Contacts API",
    description="REST API з аутентифікацією, JWT, верифікацією email, CORS, Cloudinary аватари",
    version="2.0.0"
)

# CORS
allow_origins = [o.strip() for o in (settings.CORS_ALLOW_ORIGINS or "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Створюємо таблиці (демо без Alembic)
    Base.metadata.create_all(bind=engine)
    # Легка міграція owner_id (працює на PostgreSQL; якщо свіжа БД — пропуститься)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN IF NOT EXISTS owner_id INTEGER"))
            conn.execute(text("""DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'contacts_owner_id_fkey') THEN
                    ALTER TABLE contacts ADD CONSTRAINT contacts_owner_id_fkey
                    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE;
                END IF;
            END $$;"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contacts_owner_id ON contacts (owner_id)"))
    except Exception as e:
        log.warning("Migration step failed (safe to ignore if fresh DB): %s", e)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)

# Прості шаблони UI
app.mount('/static', StaticFiles(directory=str((__file__[:-8] + '/web/static'))), name='static')
templates = Jinja2Templates(directory=str((__file__[:-8] + '/web/templates')))

@app.get('/ui')
async def ui_index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})


@app.get("/", tags=["health"])
def healthcheck():
    return {"status": "ok"}
