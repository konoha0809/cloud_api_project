from sqlalchemy.orm import Session
import tables

# --- Users ---
def get_user_by_username(db: Session, username: str):
    return db.query(tables.User).filter(tables.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(tables.User).filter(tables.User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(tables.User).all()

def create_user(db: Session, username: str, hashed_password: str):
    db_user = tables.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: tables.User):
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: tables.User):
    db.delete(user)
    db.commit()

# --- Products ---
def get_product(db: Session, product_id: int):
    return db.query(tables.Product).filter(tables.Product.id == product_id).first()

def get_all_products(db: Session):
    return db.query(tables.Product).all()

def create_product(db: Session, name: str, price: float):
    db_product = tables.Product(name=name, price=price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product: tables.Product):
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product: tables.Product):
    db.delete(product)
    db.commit()

# --- Orders ---
def get_order(db: Session, order_id: int, user_id: int):
    return db.query(tables.Order).filter(
        tables.Order.id == order_id,
        tables.Order.user_id == user_id
    ).first()

def create_order(db: Session, product_id: int, quantity: int, user_id: int):
    db_order = tables.Order(product_id=product_id, quantity=quantity, user_id=user_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order(db: Session, order: tables.Order):
    db.commit()
    db.refresh(order)
    return order

def delete_order(db: Session, order: tables.Order):
    db.delete(order)
    db.commit()