# Contacts API — Stage 2 (Auth + JWT + Ownership + Email Verify + CORS + Avatar)

## Запуск (Docker Compose)
```bash
cp .env.example .env
# за потреби змініть SECRET_KEY, CLOUDINARY_URL, SMTP_*
docker compose up -d --build
# Swagger: http://127.0.0.1:8000/docs
```

## Потік перевірки
1) `POST /auth/register` → 201 Created. Якщо email зайнятий → 409.
2) Перейди за посиланням з логів або з листа: `GET /auth/verify-email?token=...` → "Email verified".
3) `POST /auth/login` (form: `username`, `password`) → `access_token`.
4) Authorize у Swagger (Bearer).
5) CRUD `/contacts/**` — доступні лише verified користувачу та показують тільки власні контакти.
6) `GET /users/me` — з лімітами (за замовчуванням 5/хв).
7) `POST /users/me/avatar` — multipart `file`, зберігає у Cloudinary і повертає оновленого користувача.

## Нотатки
- Паролі зберігаються тільки у вигляді хешів (Passlib + bcrypt).
- JWT підписуються SECRET_KEY (з .env).
- Верифікаційні токени мають scope `email_verification` та окрему тривалість.
- CORS вмикається через `CORS_ALLOW_ORIGINS` (`*` або CSV зі списком).
- Для продакшну додайте Alembic і зовнішній rate-limit (Redis/SlowAPI).
# goit-pythonweb-hw-10


---
## Stage 3: Docs, Tests, Redis Cache, Password Reset, Roles, Token Pair, Simple UI

### Нове
- **Sphinx** документація в `docs/` (`make html`).
- **pytest** модульні та інтеграційні тести (`pytest -q --cov=app`), покриття >75% на базових сценаріях.
- **Redis** кеш: `get_current_user` читає користувача з Redis (TTL керується `CACHE_USER_TTL_SEC`).
- **Пароль reset**: `POST /auth/forgot-password?email=...` та `POST /auth/reset-password`.
- **Ролі**: поле `role` у користувача (`user`/`admin`), залежність `require_admin`.
- **Default avatar**: `POST /users/admin/default-avatar` (admin), `GET /users/default-avatar`.
- **JWT пара**: `access_token` + `refresh_token`; `POST /auth/refresh`.
- **Простий UI**: сторінка `/ui` з логіном та CRUD контактів.

### Redis
Docker Compose піднімає `redis:7`. У `.env`:
```
REDIS_URL=redis://localhost:6379/0     # локально
# або для compose: redis://redis:6379/0
CACHE_USER_TTL_SEC=300
```

### Тести
```bash
pytest -q --cov=app
```
Створюється SQLite `test.db`. Для Cloudinary тести не залежать.

### Документація
```bash
pip install sphinx
cd docs && make html && cd _build/html && python -m http.server 8001
```

### UI
Перейдіть на `http://127.0.0.1:8000/ui`.

# goit-pythonweb-hw-012
