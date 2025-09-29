from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    BackgroundTasks, 
    Request,
    Response
)
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, crud, models
from ..database import get_db
from ..security import create_access_token, create_email_token, decode_token, create_refresh_token, create_password_reset_token
from ..settings import settings
import smtplib, ssl
from email.message import EmailMessage
from email.utils import formataddr
import logging
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)

def _build_verify_url(request: Request, token: str) -> str:
    """Побудувати публічний URL верифікації за reverse-proxy (Railway)."""
    scheme = request.headers.get("x-forwarded-proto") or getattr(request.url, "scheme", "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
    return f"{scheme}://{host}/auth/verify-email?token={token}"

def send_verify_email(email: str, token: str, request: Request) -> None:
    """Надіслати лист верифікації. Підтримка STARTTLS(587) та SSL(465). 
    Якщо SMTP не налаштований/помилка — лог і м’яке продовження."""
    verify_url = _build_verify_url(request, token)

    smtp_host = settings.SMTP_HOST
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASSWORD
    smtp_port = int(settings.SMTP_PORT or 587)
    # Красивий From: або явно заданий SMTP_FROM, або сам обліковий запис
    smtp_from = getattr(settings, "SMTP_FROM", None) or smtp_user or "no-reply@example.com"

    # Формуємо лист
    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    # Якщо SMTP_FROM має вигляд "Name <email>", залишаємо як є; інакше загортаємо красиво
    if "<" in smtp_from and ">" in smtp_from:
        msg["From"] = smtp_from
    else:
        msg["From"] = formataddr(("", smtp_from))
    msg["To"] = email
    msg.set_content(f"Click to verify: {verify_url}")

    # Якщо SMTP не налаштовано — просто лог і вихід
    if not (smtp_host and smtp_user and smtp_pass):
        logging.getLogger("uvicorn.error").info("Verify link for %s: %s", email, verify_url)
        return

    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        # Успіх — дамо зрозуміти у runtime-логах
        logging.getLogger("uvicorn.error").info("Verification email sent to %s", email)
    except smtplib.SMTPAuthenticationError as e:
        log.warning("SMTP auth failed: %s. Gmail потребує App Password і повний email у SMTP_USER.", e)
        logging.getLogger("uvicorn.error").info("Verify link for %s: %s", email, verify_url)
    except Exception as e:
        log.warning("SMTP send failed, fallback to log: %s", e)
        logging.getLogger("uvicorn.error").info("Verify link for %s: %s", email, verify_url)

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, background: BackgroundTasks, request: Request,
             response: Response, db: Session = Depends(get_db)):
    try:
        user = crud.create_user(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = create_email_token(user.email)

    # Якщо SMTP не налаштовано — підкажемо лінк через заголовок + лог
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
        verify_url = _build_verify_url(request, token)
        logging.getLogger("uvicorn.error").info("Verify link for %s: %s", user.email, verify_url)
        response.headers["X-Verify-Email"] = verify_url

    # Відправка листа — у фоні; якщо впаде — лінк потрапить у лог
    background.add_task(send_verify_email, user.email, token, request)
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Логін видає пару токенів: access і refresh."""
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token(subject=user.id, scope="access")
    refresh = create_refresh_token(subject=user.id)
    # Повертаємо обидва токени; фронтенд зберігатиме refresh окремо
    return {"access_token": access, "token_type": "bearer", "refresh_token": refresh}

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    if payload.get("scope") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid token scope")
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"detail": "Already verified"}
    user.is_verified = True
    db.commit()
    return {"detail": "Email verified"}


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(body: schemas.RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("scope") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token scope")
    user_id = int(payload["sub"])
    access = create_access_token(subject=user_id, scope="access")
    return {"access_token": access, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Надсилає лінк для скидання пароля (якщо SMTP не налаштовано — пише в логи і повертає заголовок)."""
    data = request.query_params or {}
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required as query parameter")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # не розкриваємо, що користувач відсутній
        return {"detail": "If email exists, reset link will be sent"}
    token = create_password_reset_token(email)
    host = request.headers.get("host", "localhost:8000")
    link = f"http://{host}/auth/reset-password?token={token}"
    logging.getLogger("uvicorn.error").info("Password reset link for %s: %s", email, link)
    return {"detail": "Reset link generated", "reset_link": link}

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Скидання пароля за токеном."""
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    if payload.get("scope") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token scope")
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.set_password(db, user, new_password)
    return {"detail": "Password updated"}

