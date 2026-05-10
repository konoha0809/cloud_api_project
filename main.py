import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

import tables, validation, database_settings, crud
from services import UserService, ProductService, OrderService, AuthService # Імпортуємо сервіси

tables.Base.metadata.create_all(bind=database_settings.engine)

app = FastAPI(title="Cloud Commerce API")

# --- Obsługa błędów ---
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

# --- Auth ---
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-2026")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database_settings.get_db)):
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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień administratora")
    return current_user

# --- Auth endpoints ---
@app.post("/register", response_model=validation.UserOut, status_code=201)
def register(user: validation.UserCreate, db: Session = Depends(database_settings.get_db)):
    return UserService.register(db, user)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database_settings.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane logowania")
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }

# --- Admin: Users CRUD ---
@app.get("/admin/users", response_model=list[validation.UserOut])
def list_users(db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.get_all(db)

@app.get("/admin/users/{user_id}", response_model=validation.UserOut)
def get_user(user_id: int, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.get_by_id(db, user_id)

@app.put("/admin/users/{user_id}", response_model=validation.UserOut)
def edit_user(user_id: int, data: validation.UserUpdate, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.update(db, user_id, data, admin.id)

@app.delete("/admin/users/{user_id}", status_code=204)
def remove_user(user_id: int, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    UserService.delete(db, user_id, admin.id)
    return None

# --- Products CRUD ---
@app.get("/products", response_model=list[validation.ProductOut])
def get_all_products(db: Session = Depends(database_settings.get_db)):
    return ProductService.get_all(db)

@app.get("/products/{product_id}", response_model=validation.ProductOut)
def get_product(product_id: int, db: Session = Depends(database_settings.get_db)):
    return ProductService.get_by_id(db, product_id)

@app.post("/products", response_model=validation.ProductOut, status_code=201)
def add_product(product: validation.ProductCreate, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    # Zazwyczaj produkty dodaje admin, więc zmieniłem Depends na require_admin
    return ProductService.create(db, product)

@app.put("/products/{product_id}", response_model=validation.ProductOut)
def edit_product(product_id: int, data: validation.ProductUpdate, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    return ProductService.update(db, product_id, data)

@app.delete("/products/{product_id}", status_code=204)
def remove_product(product_id: int, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    ProductService.delete(db, product_id)
    return None

# --- Orders CRUD ---
@app.post("/orders", response_model=validation.OrderOut, status_code=201)
def make_order(order: validation.OrderCreate, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    return OrderService.create(db, order, current_user.id)

@app.put("/orders/{order_id}", response_model=validation.OrderOut)
def edit_order(order_id: int, data: validation.OrderUpdate, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    return OrderService.update(db, order_id, data, current_user.id)

@app.delete("/orders/{order_id}", status_code=204)
def remove_order(order_id: int, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    OrderService.delete(db, order_id, current_user.id)
    return None