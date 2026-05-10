import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

import tables, validation, crud, database_settings

tables.Base.metadata.create_all(bind=database_settings.engine)

app = FastAPI(title="Cloud Commerce API")



#Obsługa błędów

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"pole": field, "problem": error["msg"]})
    return JSONResponse(
        status_code=422,
        content={"detail": "Błąd walidacji danych", "errors": errors}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": "Wystąpił błąd serwera. Spróbuj ponownie później."}
    )

#Auth

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-2026")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database_settings.get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="Użytkownik nie istnieje")
    return user

async def require_admin(current_user=Depends(get_current_user)):
    """Dependency — дозволяє доступ тільки адмінам."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień administratora")
    return current_user

#Auth endpoints

@app.post("/register", response_model=validation.UserOut, status_code=201)
def register(user: validation.UserCreate, db: Session = Depends(database_settings.get_db)):
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Użytkownik już istnieje")
    return crud.create_user(db, user)

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database_settings.get_db)
):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane logowania")
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }

#Admin: Users CRUD

@app.get("/admin/users", response_model=list[validation.UserOut])
def list_users(
    db: Session = Depends(database_settings.get_db),
    admin=Depends(require_admin)          # ← тільки адмін
):
    return crud.get_all_users(db)

@app.get("/admin/users/{user_id}", response_model=validation.UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(database_settings.get_db),
    admin=Depends(require_admin)
):
    return crud.get_user_by_id(db, user_id)

@app.put("/admin/users/{user_id}", response_model=validation.UserOut)
def edit_user(
    user_id: int,
    data: validation.UserUpdate,
    db: Session = Depends(database_settings.get_db),
    admin=Depends(require_admin)
):
   
    if user_id == admin.id and data.role == "user":
        raise HTTPException(status_code=400, detail="Nie możesz odebrać sobie roli administratora")
    return crud.update_user(db, user_id, data)

@app.delete("/admin/users/{user_id}", status_code=204)
def remove_user(
    user_id: int,
    db: Session = Depends(database_settings.get_db),
    admin=Depends(require_admin)
):
   
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Nie możesz usunąć własnego konta")
    crud.delete_user(db, user_id)
    return None

#Products CRUD

@app.get("/products", response_model=list[validation.ProductOut])
def get_all_products(db: Session = Depends(database_settings.get_db)):
    return db.query(tables.Product).all()

@app.get("/products/{product_id}", response_model=validation.ProductOut)
def get_product(product_id: int, db: Session = Depends(database_settings.get_db)):
    return crud.get_product(db, product_id)

@app.post("/products", response_model=validation.ProductOut, status_code=201)
def add_product(
    product: validation.ProductCreate,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    return crud.create_product(db, product)

@app.put("/products/{product_id}", response_model=validation.ProductOut)
def edit_product(
    product_id: int,
    data: validation.ProductUpdate,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    return crud.update_product(db, product_id, data)

@app.delete("/products/{product_id}", status_code=204)
def remove_product(
    product_id: int,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    crud.delete_product(db, product_id)
    return None

#Orders CRUD

@app.post("/orders", response_model=validation.OrderOut, status_code=201)
def make_order(
    order: validation.OrderCreate,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    return crud.create_order(db, order, current_user.id)

@app.put("/orders/{order_id}", response_model=validation.OrderOut)
def edit_order(
    order_id: int,
    data: validation.OrderUpdate,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    return crud.update_order(db, order_id, data, current_user.id)

@app.delete("/orders/{order_id}", status_code=204)
def remove_order(
    order_id: int,
    db: Session = Depends(database_settings.get_db),
    current_user=Depends(get_current_user)
):
    crud.delete_order(db, order_id, current_user.id)
    return None