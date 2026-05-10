from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
import tables, validation

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Users

def get_user_by_username(db: Session, username: str):
    return db.query(tables.User).filter(tables.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Użytkownik o ID {user_id} nie istnieje")
    return user

def get_all_users(db: Session):
    return db.query(tables.User).all()

def create_user(db: Session, user: validation.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = tables.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, data: validation.UserUpdate):
    user = get_user_by_id(db, user_id)
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(status_code=400, detail="Nie podano żadnych danych do aktualizacji")
    if "password" in updated_fields:
        updated_fields["hashed_password"] = pwd_context.hash(updated_fields.pop("password"))
    for field, value in updated_fields.items():
        setattr(user, field, value)
    if "username" in updated_fields:
        existing = get_user_by_username(db, updated_fields["username"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Nazwa użytkownika jest już zajęta")
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#Products
def get_product(db: Session, product_id: int):
    product = db.query(tables.Product).filter(tables.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Produkt o ID {product_id} nie istnieje")
    return product

def create_product(db: Session, product: validation.ProductCreate):
    db_product = tables.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, data: validation.ProductUpdate):
    product = get_product(db, product_id)
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(status_code=400, detail="Nie podano żadnych danych do aktualizacji")
    for field, value in updated_fields.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    db.delete(product)
    db.commit()

#Orders

def get_order(db: Session, order_id: int, user_id: int):
    order = db.query(tables.Order).filter(
        tables.Order.id == order_id,
        tables.Order.user_id == user_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Zamówienie o ID {order_id} nie istnieje")
    return order

def create_order(db: Session, order: validation.OrderCreate, user_id: int):
    get_product(db, order.product_id)
    db_order = tables.Order(**order.model_dump(), user_id=user_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order(db: Session, order_id: int, data: validation.OrderUpdate, user_id: int):
    order = get_order(db, order_id, user_id)
    order.quantity = data.quantity
    db.commit()
    db.refresh(order)
    return order

def delete_order(db: Session, order_id: int, user_id: int):
    order = get_order(db, order_id, user_id)
    db.delete(order)
    db.commit()