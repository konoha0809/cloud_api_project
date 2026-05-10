from sqlalchemy.orm import Session
from passlib.context import CryptContext
import tables, validation 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(tables.User).filter(tables.User.username == username).first()

def create_user(db: Session, user: validation.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = tables.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_product(db: Session, product: validation.ProductCreate):
    db_product = tables.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_order(db: Session, order: validation.OrderCreate, user_id: int):
    db_order = tables.Order(**order.model_dump(), user_id=user_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order