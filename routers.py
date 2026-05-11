from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import validation, database_settings, crud
from services import UserService, ProductService, OrderService, AuthService
from security import create_access_token, get_current_user, require_admin

router = APIRouter()

# --- Auth ---
@router.post("/register", response_model=validation.UserOut, status_code=201, tags=["Auth"])
def register(user: validation.UserCreate, db: Session = Depends(database_settings.get_db)):
    return UserService.register(db, user)

@router.post("/login", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database_settings.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane logowania")
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }

# --- Admin: Users ---
@router.get("/admin/users", response_model=list[validation.UserOut], tags=["Admin Users"])
def list_users(db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.get_all(db)

@router.get("/admin/users/{user_id}", response_model=validation.UserOut, tags=["Admin Users"])
def get_user(user_id: int, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.get_by_id(db, user_id)

@router.put("/admin/users/{user_id}", response_model=validation.UserOut, tags=["Admin Users"])
def edit_user(user_id: int, data: validation.UserUpdate, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    return UserService.update(db, user_id, data, admin.id)

@router.delete("/admin/users/{user_id}", status_code=204, tags=["Admin Users"])
def remove_user(user_id: int, db: Session = Depends(database_settings.get_db), admin=Depends(require_admin)):
    UserService.delete(db, user_id, admin.id)
    return None

# --- Products ---
@router.get("/products", response_model=list[validation.ProductOut], tags=["Products"])
def get_all_products(db: Session = Depends(database_settings.get_db)):
    return ProductService.get_all(db)

@router.get("/products/{product_id}", response_model=validation.ProductOut, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(database_settings.get_db)):
    return ProductService.get_by_id(db, product_id)

@router.post("/products", response_model=validation.ProductOut, status_code=201, tags=["Products"])
def add_product(product: validation.ProductCreate, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    return ProductService.create(db, product)

@router.put("/products/{product_id}", response_model=validation.ProductOut, tags=["Products"])
def edit_product(product_id: int, data: validation.ProductUpdate, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    return ProductService.update(db, product_id, data)

@router.delete("/products/{product_id}", status_code=204, tags=["Products"])
def remove_product(product_id: int, db: Session = Depends(database_settings.get_db), current_user=Depends(require_admin)):
    ProductService.delete(db, product_id)
    return None

# --- Orders ---
@router.post("/orders", response_model=validation.OrderOut, status_code=201, tags=["Orders"])
def make_order(order: validation.OrderCreate, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    return OrderService.create(db, order, current_user.id)

@router.put("/orders/{order_id}", response_model=validation.OrderOut, tags=["Orders"])
def edit_order(order_id: int, data: validation.OrderUpdate, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    return OrderService.update(db, order_id, data, current_user.id)

@router.delete("/orders/{order_id}", status_code=204, tags=["Orders"])
def remove_order(order_id: int, db: Session = Depends(database_settings.get_db), current_user=Depends(get_current_user)):
    OrderService.delete(db, order_id, current_user.id)
    return None